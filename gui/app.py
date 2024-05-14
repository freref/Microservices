from flask import Flask, render_template, redirect, request, make_response
import requests
from flasgger import Swagger

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/",
}

app = Flask(__name__)
swagger = Swagger(app, config=swagger_config)

AUTH_SERVICE_URL = "http://auth:5000"
EVENTS_SERVICE_URL = "http://events:5000"
INVITATIONS_SERVICE_URL = "http://invitations:5000"
CALENDARS_SERVICE_URL = "http://calendars:5000"

# The Username & Password of the currently logged-in User, this is used as a pseudo-cookie, as such this is not session-specific.
username = None
password = None

session_data = dict()


def save_to_session(key, value):
    session_data[key] = value


def load_from_session(key):
    return (
        session_data.pop(key) if key in session_data else None
    )  # Pop to ensure that it is only used once


def succesful_request(r):
    return r.status_code == 200 or r.status_code == 201


@app.route("/")
def home():
    global username, password
    if username is None:
        return render_template("login.html", username=username, password=password)
    else:
        params = {"is_public": True}
        try:
            response = requests.get(f"{EVENTS_SERVICE_URL}/events/", params=params)
            # if the request fails, return the home page with an empty list of events
            if response.status_code != 200:
                return make_response(
                    render_template(
                        "home.html", username=username, password=password, events=[]
                    ),
                    response.status_code,
                )
        except:
            return make_response(
                render_template(
                    "home.html", username=username, password=password, events=[]
                ),
                400,
            )

        # Destructure the response to get the events
        events = response.json().get("events", [])
        public_events = [
            (event["title"], event["date"], event["organizer"]) for event in events
        ]

        return make_response(
            render_template(
                "home.html", username=username, password=password, events=public_events
            ),
            200,
        )


@app.route("/event", methods=["POST"])
def create_event():
    """
    Create an event
    ---
    tags:
        - Events
    parameters:
        - name: title
          in: formData
          type: string
          required: true
        - name: description
          in: formData
          type: string
          required: true
        - name: date
          in: formData
          type: string
          required: true
        - name: publicprivate
          in: formData
          type: string
          required: true
        - name: invites
          in: formData
          type: string
          required: false
    responses:
        201:
            description: Event created
        400:
            description: Event creation failed
    """
    global username, password
    title, description, date, publicprivate, invites = (
        request.form["title"],
        request.form["description"],
        request.form["date"],
        request.form["publicprivate"],
        request.form["invites"],
    )

    try:
        response = requests.post(
            f"{EVENTS_SERVICE_URL}/events/",
            json={
                "date": date,
                "organizer": username,
                "title": title,
                "description": description,
                "is_public": publicprivate == "public",
            },
        )
        if response.status_code != 201:
            return redirect("/")
    except:
        return redirect("/")

    event_id = response.json().get("event_id", None)
    invitees = invites.split(";")

    for invitee in invitees:
        invitee = invitee.strip()
        if invitee:
            try:
                response = requests.post(
                    f"{INVITATIONS_SERVICE_URL}/invitations/",
                    json={
                        "event_id": event_id,
                        "invitee": invitee,
                        "status": "Pending",
                    },
                )
                if response.status_code != 201:
                    return redirect("/")
            except:
                return redirect("/")

    # Invite yourself and set status to Participate
    if username not in invitees:
        try:
            response = requests.post(
                f"{INVITATIONS_SERVICE_URL}/invitations/",
                json={
                    "event_id": event_id,
                    "invitee": username,
                    "status": "Participate",
                },
            )
        finally:
            return redirect("/")

    return redirect("/")


@app.route("/calendar", methods=["GET", "POST"])
def calendar():
    global username, password
    calendar_user = (
        request.form["calendar_user"] if "calendar_user" in request.form else username
    )

    if calendar_user is not username:
        try:
            calendar_response = requests.get(
                f"{CALENDARS_SERVICE_URL}/calendars/", params={"owner": calendar_user}
            )

            # if the request fails, return the calendar page with an empty list of events
            if calendar_response.status_code != 200:
                return render_template(
                    "calendar.html",
                    username=username,
                    password=password,
                    calendar_user=calendar_user,
                    calendar=[],
                    success=False,
                )
        except:
            return render_template(
                "calendar.html",
                username=username,
                password=password,
                calendar_user=calendar_user,
                calendar=[],
                success=False,
            )

        success = username in calendar_response.json().get("shared_with", [])
    else:
        success = True

    params = {"invitee": calendar_user, "status": "Participate"}
    try:
        participating_events = requests.get(
            f"{INVITATIONS_SERVICE_URL}/invitations/", params=params
        )
        if participating_events.status_code != 200:
            my_invites = []
        else:
            my_invites = participating_events.json().get("invitations", [])
    except:
        my_invites = []

    params = {"invitee": calendar_user, "status": "Maybe Participate"}

    try:
        maybe_participating_events = requests.get(
            f"{INVITATIONS_SERVICE_URL}/invitations/",
            params=params,
        )
        if maybe_participating_events.status_code != 200:
            my_invites += []
        else:
            my_invites += maybe_participating_events.json().get("invitations", [])
    except:
        my_invites += []

    if success:
        calendar = []
        for invite in my_invites:
            event_id = invite["event_id"]
            params = {"id": event_id}
            try:
                event_response = requests.get(
                    f"{EVENTS_SERVICE_URL}/events/",
                    params=params,
                )
            except:
                continue

            if event_response.status_code == 200:
                event = event_response.json().get("events", [])[0]
                calendar.append(
                    (
                        event_id,
                        event["title"],
                        event["date"],
                        event["organizer"],
                        invite["status"],
                        "Public" if event["is_public"] else "Private",
                    )
                )
    else:
        calendar = None

    return render_template(
        "calendar.html",
        username=username,
        password=password,
        calendar_user=calendar_user,
        calendar=calendar,
        success=success,
    )


@app.route("/share", methods=["GET"])
def share_page():
    global username, password
    return render_template(
        "share.html", username=username, password=password, success=None
    )


@app.route("/share", methods=["POST"])
def share():
    global username, password
    share_user = request.form["username"]

    try:
        response = requests.put(
            f"{CALENDARS_SERVICE_URL}/share",
            json={"owner": username, "shared_with": share_user},
        )
        success = succesful_request(response)
    except:
        success = False

    return render_template(
        "share.html", username=username, password=password, success=success
    )


@app.route("/event/<eventid>")
def view_event(eventid):
    global username, password
    params = {"event": eventid}

    try:
        invitations_response = requests.get(
            f"{INVITATIONS_SERVICE_URL}/invitations/",
            params=params,
        )
        if invitations_response.status_code != 200:
            invitations = []
        else:
            invitations = invitations_response.json().get("invitations", [])
    except:
        invitations = []

    success = username in [invite["invitee"] for invite in invitations]

    params = {"id": eventid}

    try:
        event_response = requests.get(
            f"{EVENTS_SERVICE_URL}/events/",
            params=params,
        )
        if event_response.status_code != 200:
            return render_template(
                "event.html",
                username=username,
                password=password,
                event={},
                success=success,
            )
        else:
            event = event_response.json().get("events", [])[0]
    except:
        return render_template(
            "event.html",
            username=username,
            password=password,
            event={},
            success=success,
        )
    success = success or event["is_public"]

    if success:
        # event info is a list of [title, date, organizer, status, [(invitee, participating)]]
        event = (
            event["title"],
            event["date"],
            event["organizer"],
            "Public" if event["is_public"] else "Private",
            [(invite["invitee"], invite["status"]) for invite in invitations],
        )
    else:
        event = None  # No success, so don't fetch the data

    return render_template(
        "event.html", username=username, password=password, event=event, success=success
    )


@app.route("/login", methods=["POST"])
def login():
    """
    User Login
    ---
    tags:
        - Auth
    parameters:
        - name: username
          in: formData
          type: string
          required: true
        - name: password
          in: formData
          type: string
          required: true
    responses:
        200:
            description: Login successful
        401:
            description: Login failed
    """
    global username, password
    req_username, req_password = request.form["username"], request.form["password"]

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/login/",
            json={"username": req_username, "password": req_password},
        )
        success = succesful_request(response)
    except:
        return make_response(
            render_template(
                "login.html",
                username=username,
                password=password,
                success=False,
                login=True,
            ),
            401,
        )

    save_to_session("success", success)

    if success:
        username = req_username
        password = req_password

    return make_response(
        render_template(
            "login.html",
            username=username,
            password=password,
            success=success,
            login=True,
        ),
        200,
    )


@app.route("/register", methods=["POST"])
def register():
    """
    User Registration
    ---
    tags:
        - Auth
    parameters:
        - name: username
          in: formData
          type: string
          required: true
        - name: password
          in: formData
          type: string
          required: true
    responses:
        201:
            description: Registration successful
        400:
            description: Registration failed
    """
    global username, password
    req_username, req_password = request.form["username"], request.form["password"]

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register/",
            json={"username": req_username, "password": req_password},
        )
        success = succesful_request(response)
    except:
        return make_response(
            render_template(
                "login.html",
                username=username,
                password=password,
                success=False,
                registration=True,
            ),
            400,
        )

    save_to_session("success", success)

    if success:
        username = req_username
        password = req_password

    return make_response(
        render_template(
            "login.html",
            username=username,
            password=password,
            success=success,
            registration=True,
        ),
        200,
    )


@app.route("/invites", methods=["GET"])
def invites():
    global username, password
    params = {"invitee": username, "status": "Pending"}

    try:
        response = requests.get(
            f"{INVITATIONS_SERVICE_URL}/invitations/",
            params=params,
        )
        if response.status_code != 200:
            my_invites = []
        else:
            my_invites = response.json().get("invitations", [])
    except:
        my_invites = []

    invites = []
    for invite in my_invites:
        event_id = invite["event_id"]
        params = {"id": event_id}
        try:
            event_response = requests.get(
                f"{EVENTS_SERVICE_URL}/events/",
                params=params,
            )

            if event_response.status_code == 200:
                event = event_response.json().get("events", [])[0]
                invites.append(
                    (
                        event_id,
                        event["title"],
                        event["date"],
                        event["organizer"],
                        event["is_public"],
                    )
                )
        except:
            continue

    return make_response(
        render_template(
            "invites.html", username=username, password=password, invites=invites
        ),
        200,
    )


@app.route("/invites", methods=["POST"])
def process_invite():
    global username, password
    eventId, status = request.json["event"], request.json["status"]

    params = {"invitee": username, "event": eventId, "status": status}
    try:
        requests.patch(
            f"{INVITATIONS_SERVICE_URL}/invitations/{eventId}/{username}",
            params=params,
        )
    except:
        return redirect("/invites")

    return redirect("/invites")


@app.route("/logout")
def logout():
    global username, password

    username = None
    password = None
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
