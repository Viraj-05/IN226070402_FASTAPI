from fastapi import FastAPI , HTTPException, status , Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()
            

plans = [
    {"id": 1, "name": "Basic", "duration_months": 1, "price": 1200, "includes_classes": False, "includes_trainer": False},
    {"id": 2, "name": "Standard", "duration_months": 3, "price": 3000, "includes_classes": True, "includes_trainer": False},
    {"id": 3, "name": "Premium", "duration_months": 6, "price": 5500, "includes_classes": True, "includes_trainer": True},
    {"id": 4, "name": "Elite", "duration_months": 12, "price": 8000, "includes_classes": True, "includes_trainer": True},
    {"id": 5, "name": "Pro", "duration_months": 9, "price": 6500, "includes_classes": True, "includes_trainer": False},
]

memberships = []
membership_counter = 1

class_bookings = []
class_counter = 1


class EnrollRequest (BaseModel):
    member_name: str = Field(min_length = 2)
    plan_id: int = Field(gt = 0)
    phone : str = Field (min_length = 10)
    start_month : str = Field(min_length = 3 )
    payment_mode : str = "cash"
    referral_code : str = ""

class NewPlan(BaseModel):
    name : str = Field(min_lngth = 2)
    duration_months : int = Field(gt = 0)
    price : int = Field(gt = 0)
    includes_classes : bool = False
    includes_trainer : bool = False


class ClassBooking(BaseModel):
    member_name: str
    class_name : str
    class_dates : str


def find_plan(plan_id):
    for p in plans:
        if p["id"] == plan_id:
            return p 
    return None

def calculate_membership_fee(price, duration,  payment_mode, referral_code):
    discount = 0
    breakdown = []

    if duration >= 12:
        discount += 20
        breakdown.append("20% ( 12 months)")
    elif duration >= 6:
        discount += 10
        breakdown.append("10% (6+ months)")


    if referral_code:
        discount += 5
        breakdown.append("5% referral ")

    total = price
    total = total - (total * discount / 100)

    if payment_mode == "emi":
        total += 200
        breakdown.append("₹200 EMI fee")

    return total , breakdown

# Question 1 - 5 
@app.get("/")
def home():
    return {"message" : "Welcome to FitNest Gym "}


@app.get("/plans")
def get_plans():
    prices = [p["price"] for p in plans]
    return {
        "plans": plans,
        "total": len(plans),
        "min_price": min(prices),
        "max_price": max(prices)
    }

@app.get("/plans/summary")
def plans_summary():
    return  {
        "total_plans": len(plans),
        "with_classes": sum(1 for p in plans if p["includes_classes"]),
        "with_trainer": sum(1 for p in plans if p["includes_trainer"]),
        "cheapest": min(plans, key=lambda x: x["price"]),
        "expensive": max(plans, key=lambda x: x["price"])
    }

@app.get("/plans/filter")
def filter_plans(
    max_price : Optional[int] = None,
    max_duration : Optional [int] = None,
    includes_classes : Optional [bool] = None,
    includes_trainer : Optional [bool] = None
):
    result = plans

    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    
    if max_duration is not None :
        result = [p for p in result if p["duration_months"] <= max_duration]

    if includes_classes is not None :
        result = [p for p in result if p["includes_classes"] == includes_classes]

    if includes_trainer is not None:
        result = [p for p in result if p["includes_trainer"] == includes_trainer ]

    return result


@app.get("/plans/search")
def search_plans(keyword: str):
    keyword = keyword.lower()
    result = [
        p for p in plans
        if keyword in p["name"].lower()
        or (keyword == "classes" and p["includes_classes"])
        or (keyword == "trainer" and p["includes_trainer"])
    ]
    return {"results": result, "total_found": len(result)}

@app.get("/plans/sort")
def sort_plans(sort_by: str = "price"):
    if sort_by not in ["price", "name", "duration_months"]:
        raise HTTPException (status_code=400, detail = "Invalid sort_by")
    
    return sorted(plans, key=lambda x: x[sort_by])

@app.get("/plans/page")
def pagination_plans(page: int = 1, limit : int = 2):
    start = (page - 1) * limit
    end = start + limit

    return {
        "data": plans[start:end],
        "total_pages": (len(plans) + limit - 1) // limit
    }



@app.get("/plans/browse")
def browse_plans(
    keyword: Optional[str] = None,
    includes_classes: Optional[bool] = None,
    includes_trainer: Optional[bool] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 2
):
    result = plans

    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]

    if includes_classes is not None:
        result = [p for p in result if p["includes_classes"] == includes_classes]

    if includes_trainer is not None:
        result = [p for p in result if p["includes_trainer"] == includes_trainer]

    if sort_by in ["price", "name", "duration_months"]:
        result = sorted(result, key=lambda x: x[sort_by], reverse=(order == "desc"))

    start = (page - 1) * limit
    end = start + limit

    return {
        "data": result[start:end],
        "total": len(result),
        "total_pages": (len(result) + limit - 1) // limit
    }


@app.get("/plans/{plan_id}")
def get_plan(plan_id : int):
  plan = find_plan(plan_id)
  if not plan:
      raise HTTPException(status_code=404, detail="Plan not found")
  return plan


@app.get("/memberships")
def get_memberships():
    return {"memberships": memberships, "total": len(memberships)}



# Q8,9 POST MEMBERSHIP
@app.post("/memberships", status_code=201)
def create_membership(data: EnrollRequest):
    global membership_counter

    plan = find_plan(data.plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    total, breakdown = calculate_membership_fee(
        plan["price"],
        plan["duration_months"],
        data.payment_mode,
        data.referral_code
    )

    membership = {
        "id": membership_counter,
        "member_name": data.member_name,
        "plan_name": plan["name"],
        "duration": plan["duration_months"],
        "total_fee": total,
        "discount_breakdown": breakdown,
        "status": "active"
    }

    memberships.append(membership)
    membership_counter += 1

    return membership

# Question 11 CREATE PLAN
@app.post("/plans", status_code=201)
def create_plan(plan: NewPlan):
    global plans
    for p in plans:
        if p["name"].lower() == plan.name.lower():
            raise HTTPException(400, "Duplicate plan")

    new = plan.model_dump()
    new["id"] = len(plans) + 1
    plans.append(new)

    return new

# Question 12 UPDATE PLAN
@app.put("/plans/{plan_id}")
def update_plan(
    plan_id: int,
    price: Optional[int] = None,
    includes_classes: Optional[bool] = None,
    includes_trainer: Optional[bool] = None
):
    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Not found")

    if price is not None:
        plan["price"] = price
    if includes_classes is not None:
        plan["includes_classes"] = includes_classes
    if includes_trainer is not None:
        plan["includes_trainer"] = includes_trainer

    return plan

# Question 13 DELETE PLAN
@app.delete("/plans/{plan_id}")
def delete_plan(plan_id: int):
    global plans

    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Not found")

    for m in memberships:
        if m["plan_name"] == plan["name"]:
            raise HTTPException(400, "Active memberships exist")

    plans = [p for p in plans if p["id"] != plan_id]

    return {"message": "Deleted"}

# Q14 CLASS BOOKING
@app.post("/classes/book")
def book_class(data: ClassBooking):
    global class_counter

    for m in memberships:
        if m["member_name"] == data.member_name and m["status"] == "active":
            booking = {
                "id": class_counter,
                "member_name": data.member_name,
                "class_name": data.class_name,
                "date": data.class_dates
            }
            class_bookings.append(booking)
            class_counter += 1
            return booking

    raise HTTPException(400, "No active membership")

@app.get("/classes/bookings")
def get_bookings():
    return class_bookings

# Question 15 Cancel, Freeze , reactivate
@app.delete("/classes/cancel/{booking_id}")
def cancel_booking(booking_id: int):
    global class_bookings
    class_bookings = [b for b in class_bookings if b["id"] != booking_id]
    return {"message": "Cancelled"}

@app.put("/memberships/{id}/freeze")
def freeze(id: int):
    for m in memberships:
        if m["id"] == id:
            m["status"] = "frozen"
            return m
    raise HTTPException(404, "Not found")

@app.put("/memberships/{id}/reactivate")
def reactivate(id: int):
    for m in memberships:
        if m["id"] == id:
            m["status"] = "active"
            return m
    raise HTTPException(404, "Not found")

# Question 19 
@app.get("/memberships/search")
def search_memberships(keyword: str):
    keyword = keyword.lower()

    result = [
        m for m in memberships
        if keyword in m["member_name"].lower()
    ]

    return {
        "results": result,
        "total_found": len(result)
    }

@app.get("/memberships/sort")
def sort_memberships(sort_by: str = "total_fee"):
    if sort_by not in ["total_fee", "duration"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    return sorted(memberships, key=lambda x: x[sort_by])

@app.get("/memberships/page")
def paginate_memberships(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit

    return {
        "data": memberships[start:end],
        "total_pages": (len(memberships) + limit - 1) // limit
    }