from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-secret-key-for-your-project"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLIGHTS_FILE = os.path.join(BASE_DIR, "flights.json")
BOOKINGS_FILE = os.path.join(BASE_DIR, "bookings.json")


def read_json(path, default):
    """Read JSON data safely; create the file with default data if it does not exist."""
    if not os.path.exists(path):
        write_json(path, default)
        return default
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def get_flights():
    return read_json(FLIGHTS_FILE, [])


def save_flights(flights):
    write_json(FLIGHTS_FILE, flights)


def get_bookings():
    return read_json(BOOKINGS_FILE, {"bookings": [], "next_id": 1001})


def save_bookings(data):
    write_json(BOOKINGS_FILE, data)


def search_flights(source="", destination="", airline=""):
    """Linear search: inspect each flight and retain records matching the filters."""
    results = []
    for flight in get_flights():
        if flight.get("seats", 0) <= 0:
            continue
        if source and source.casefold() not in flight["source"].casefold():
            continue
        if destination and destination.casefold() not in flight["destination"].casefold():
            continue
        if airline and airline.casefold() not in flight["airline"].casefold():
            continue
        results.append(flight)
    return results


@app.route("/")
def home():
    flights = [f for f in get_flights() if f.get("seats", 0) > 0]
    return render_template("index.html", flights=flights[:3])


@app.route("/flights")
def flights_page():
    source = request.args.get("source", "").strip()
    destination = request.args.get("destination", "").strip()
    airline = request.args.get("airline", "").strip()
    sort_by = request.args.get("sort", "fare")

    results = search_flights(source, destination, airline)

    # Sorting operations for the Data Structures mini-project.
    if sort_by == "departure":
        results.sort(key=lambda f: f["departure"])
    elif sort_by == "seats":
        results.sort(key=lambda f: f["seats"], reverse=True)
    elif sort_by == "airline":
        results.sort(key=lambda f: f["airline"].casefold())
    else:
        sort_by = "fare"
        results.sort(key=lambda f: f["fare"])

    return render_template(
        "flights.html",
        flights=results,
        source=source,
        destination=destination,
        airline=airline,
        sort_by=sort_by,
    )


@app.route("/book/<flight_no>", methods=["POST"])
def book_flight(flight_no):
    flights = get_flights()
    flight = next((f for f in flights if f["flight_no"] == flight_no), None)

    if flight is None or flight.get("seats", 0) <= 0:
        flash("This flight is unavailable or has no seats left.", "error")
        return redirect(url_for("flights_page"))

    passenger = request.form.get("passenger", "").strip()
    contact = request.form.get("contact", "").strip()

    if not passenger:
        flash("Please enter the passenger's full name.", "error")
        return redirect(url_for("flights_page"))
    if not contact.isdigit() or not (7 <= len(contact) <= 15):
        flash("Enter a contact number containing 7 to 15 digits.", "error")
        return redirect(url_for("flights_page"))

    booking_data = get_bookings()
    booking_id = f"BK{booking_data.get('next_id', 1001)}"
    booking_data["next_id"] = int(booking_data.get("next_id", 1001)) + 1

    booking = {
        "booking_id": booking_id,
        "passenger": passenger,
        "contact": contact,
        "flight_no": flight["flight_no"],
        "airline": flight["airline"],
        "route": f"{flight['source']} → {flight['destination']}",
        "source": flight["source"],
        "destination": flight["destination"],
        "departure": flight["departure"],
        "fare": flight["fare"],
        "status": "Confirmed",
        "created_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }
    booking_data["bookings"].append(booking)
    flight["seats"] -= 1

    save_bookings(booking_data)
    save_flights(flights)
    return render_template("booking_confirmation.html", booking=booking)


@app.route("/bookings")
def bookings_page():
    data = get_bookings()
    bookings = list(reversed(data.get("bookings", [])))
    return render_template("bookings.html", bookings=bookings)


@app.route("/cancel/<booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    data = get_bookings()
    booking = next(
        (b for b in data.get("bookings", []) if b["booking_id"].casefold() == booking_id.casefold()),
        None,
    )

    if booking is None:
        flash("Booking ID was not found.", "error")
        return redirect(url_for("bookings_page"))
    if booking.get("status") == "Cancelled":
        flash("This booking has already been cancelled.", "error")
        return redirect(url_for("bookings_page"))

    booking["status"] = "Cancelled"
    flights = get_flights()
    flight = next((f for f in flights if f["flight_no"] == booking["flight_no"]), None)
    if flight:
        flight["seats"] += 1
        save_flights(flights)

    save_bookings(data)
    flash(f"Booking {booking_id} cancelled. One seat has been restored.", "success")
    return redirect(url_for("bookings_page"))


if __name__ == "__main__":
    # Debug mode is useful during local development. Do not use it on a public production server.
    app.run(debug=True)
