import json
import sqlite3
from utils.database_setup import get_db_connection

class User:
    def __init__(self, userid=None, name=None, email=None, budget=None, travel_days=None, password=None):
        self.userid = userid
        self.name = name
        self.email = email
        self.budget = budget
        self.travel_days = travel_days
        self.password = password

    @staticmethod
    def login(username, password):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM User WHERE name=? AND password=?", (username, password))
        row = cur.fetchone()
        conn.close()
        if row:
            return User(userid=row['user_id'], name=row['name'], email=row['email'], budget=row['budget'], travel_days=row['travel_days'])
        return None

    @staticmethod
    def create(username, password, email=None):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO User (name, password, email) VALUES (?, ?, ?)", (username, password, email))
            conn.commit()
            return True
        except Exception as e:
            print("Error creating user:", e)
            return False
        finally:
            conn.close()

    def enterPreferences(self, budget, travel_days, place_types="", season=""):
        """Save user preferences including numeric budget, place types, and season."""
        self.budget = budget
        self.travel_days = travel_days
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE User SET budget=?, travel_days=?, place_types=?, season=? WHERE user_id=?",
            (budget, travel_days, place_types, season, self.userid)
        )
        conn.commit()
        conn.close()

    def viewRecommendations(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM TravelPlan WHERE user_id=?", (self.userid,))
        plans = cur.fetchall()
        conn.close()
        return plans


class Destination:
    def __init__(self, name, category, cost_exp, details=""):
        self.name = name
        self.category = category
        self.cost_exp = cost_exp
        self.details = details

    @staticmethod
    def get_by_name(name):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # Find exact or similar destination
            cur.execute("SELECT * FROM Destination WHERE name LIKE ?", ('%' + name + '%',))
            row = cur.fetchone()
            conn.close()
        except sqlite3.Error as e:
            print("⚠ Destination lookup skipped:", e)
            return None
        if row:
            return Destination(row['name'], row['type'], row['average_cost'])
        return None


class Accommodation:
    def __init__(self, acc_id, name, price, location):
        self.acc_id = acc_id
        self.name = name
        self.price = price
        self.location = location

    @staticmethod
    def get_by_location(location):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Accommodation WHERE location LIKE ?", ('%' + location + '%',))
        rows = cur.fetchall()
        conn.close()
        return [Accommodation(r['accommodation_id'], r['name'], r['price'], r['location']) for r in rows]


class TravelPlan:
    def __init__(self, planid=None, dest=None, stay_cost=0, duration=0, accommodations=None):
        self.planid = planid
        self.dest = dest
        self.stay_cost = stay_cost
        self.duration = duration
        self.accommodations = accommodations if accommodations else []

    @staticmethod
    def createPlan(user_id, destination_name, duration, total_cost, 
                   interest="", place_types="", season="", travel_mode="",
                   itinerary_json="", accommodation_id=None, start_date="", end_date=""):
        """Create a travel plan with full itinerary data for history."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Ensure Destination exists or create it
        cur.execute("SELECT destination_id FROM Destination WHERE name=?", (destination_name,))
        dest_row = cur.fetchone()
        if dest_row:
            dest_id = dest_row['destination_id']
        else:
            cur.execute("INSERT INTO Destination (name, type, average_cost) VALUES (?, ?, ?)", (destination_name, "Custom", total_cost))
            dest_id = cur.lastrowid
            
        # 2. Insert TravelPlan with all new fields
        cur.execute(
            """INSERT INTO TravelPlan 
               (user_id, destination_id, destination_name, total_cost, duration, 
                interest, place_types, season, travel_mode, itinerary_json, start_date, end_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
            (user_id, dest_id, destination_name, total_cost, duration,
             interest, place_types, season, travel_mode, itinerary_json, start_date, end_date)
        )
        plan_id = cur.lastrowid
        
        # 3. Create Booking if accommodation provided
        if accommodation_id:
            cur.execute("INSERT INTO Booking (user_id, accommodation_id, plan_id, stay_days) VALUES (?, ?, ?, ?)",
                        (user_id, accommodation_id, plan_id, duration))
            
        conn.commit()
        conn.close()
        return plan_id

    @staticmethod
    def getUserHistory(user_id):
        """Get all saved travel plans for a user, newest first."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """SELECT plan_id, destination_name, total_cost, duration, interest, 
                      place_types, season, travel_mode, itinerary_json, start_date, end_date, created_at
               FROM TravelPlan WHERE user_id=? ORDER BY created_at DESC""",
            (user_id,)
        )
        rows = cur.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            item = {
                "plan_id": row["plan_id"],
                "destination": row["destination_name"] or "Unknown",
                "cost": row["total_cost"],
                "duration": row["duration"],
                "interest": row["interest"] or "",
                "place_types": row["place_types"] or "",
                "season": row["season"] or "",
                "travel_mode": row["travel_mode"] or "",
                "start_date": row["start_date"] or "",
                "end_date": row["end_date"] or "",
                "created_at": row["created_at"] or "",
                "itinerary": None
            }
            if row["itinerary_json"]:
                try:
                    item["itinerary"] = json.loads(row["itinerary_json"])
                except json.JSONDecodeError:
                    item["itinerary"] = None
            history.append(item)
        return history

    @staticmethod
    def deletePlan(plan_id, user_id):
        """Delete a saved travel plan."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM TravelPlan WHERE plan_id=? AND user_id=?", (plan_id, user_id))
        conn.commit()
        conn.close()

    def updatePlan(self):
        pass


class RecommendationEngine:
    @staticmethod
    def analyzePreferences(budget, travel_days, interest, place_types="", season=""):
        """Convert preferences into constraints using numeric budget."""
        constraints = {
            "max_budget": float(budget) if budget else 5000,
            "days": int(travel_days),
            "type": interest,
            "place_types": place_types,
            "season": season
        }
        return constraints

    @staticmethod
    def matchDestinationData(location, constraints):
        # DFD 2.3: Check DB for destinations
        dest = Destination.get_by_name(location)
        if dest and dest.cost_exp > constraints["max_budget"]:
            print(f"Warning: {location} average cost exceeds budget!")
        return dest

    @staticmethod
    def suggestDestinations(location, interest, budget, travel_mode, duration, place_types="", season="", start_date="", end_date=""):
        """Get 5 destination suggestions from AI."""
        from model.recommender import get_recommendations

        constraints = RecommendationEngine.analyzePreferences(budget, duration, interest, place_types, season)
        RecommendationEngine.matchDestinationData(location, constraints)
        return get_recommendations(location, interest, budget, travel_mode, duration, place_types, season, start_date, end_date)
        
    @staticmethod
    def optimizeBudget(plan):
        # DFD 2.5: Advanced feature for future
        pass


class Admin:
    @staticmethod
    def manageUsers():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, name, email FROM User")
        users = cur.fetchall()
        conn.close()
        return users

    @staticmethod
    def manageDestinations():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Destination")
        dests = cur.fetchall()
        conn.close()
        return dests

    @staticmethod
    def checkAvail(destination_name):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Accommodation WHERE location=?", (destination_name,))
        accs = cur.fetchall()
        conn.close()
        return accs
