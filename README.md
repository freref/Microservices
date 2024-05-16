# DS Microservices Report

## Running the Project
You can start the project by using the `run.sh` shell script. The frontend will then be accessible at [http://localhost:5001/](http://localhost:5001/).
### Using Docker
```sh
docker compose up --build
```
### Using Podman
If you prefer to use Podman, first pull the required image due to rate limiting issues experienced with Podman:
```sh
podman pull python:3.12-rc-slim-buster
```
Then build the and start the project with:
```sh
podman compose up --build
```
## Architecture
### Microservices
#### Auth
##### Features
- POST ``/register`` implements registering an account if the user doesn't already exist
- POST ``/login`` implements logging in if the user is registered
##### Data
```sql
id SERIAL PRIMARY KEY,
username VARCHAR(50) NOT NULL UNIQUE,
password VARCHAR(255) NOT NULL
```
##### Reasoning
Register and login both need access to the same data, so I grouped them together. When this service fails logging in and registering won't work anymore. If you're already logged in everything will continue to work since it is stored in the session.
#### Events
##### Features
- POST ``/events`` implements creating a new event, this is used in the home page.
- GET ``/events`` implements retrieving events given the following optional filters: ``is_public``, ``id``. This is used on the homepage to retrieve all the public events using the ``is_public`` filter. It is used to retrieve all the events you're invited to and (maybe attending) using the ``id`` filter (invitations are kept by the invitation service). This is used to retrieve event information when you click the event in the Calendar tab using the ``id`` filter, before you can view this it checks if it is public or if you're invited. At last it is also used to show the events in the Invites tab similarly to the Calendar tab, but here it is only events you haven't yet responded to.
##### Data
```sql
id SERIAL PRIMARY KEY,
date DATE NOT NULL,
organizer VARCHAR(100) NOT NULL,
title VARCHAR(100) NOT NULL,
description TEXT,
is_public BOOLEAN NOT NULL
```
##### Reasoning
The Events service manages all event-related data, allowing for efficient retrieval and creation of events. By separating event data from other concerns, it ensures that event management is scalable and independent. If this service fails, users won't be able to create or view event details.
#### Invitations
##### Features
- POST ``/invitations`` implements creating a single invite, the endpoint is repeatedly called for each use you invite when creating an event
- GET ``/invitations`` implements retrieving invites given the following filters: ``invitee``, ``status`` and ``event``. This is used to check which events you're going to (maybe) participate in using the ``status`` and ``invitee`` filter in Calendar. This is used to check if you're allowed to view a private event by checking if you're invited. At last this is used to check which events you're invited to in the Invites tab. It then retrieves the information of the event using the ``events`` service.
- PATCH ``/invitations/{event_id}/{invitee}`` implements updating the status of an invite, this is used to respond to invites, updating the status from ``Pending`` to ``Participate``, ``Maybe Participate`` or ``Don't Participate``.
##### Data
```sql
event_id INT NOT NULL,
invitee VARCHAR(100) NOT NULL,
status VARCHAR(20) NOT NULL,
PRIMARY KEY (event_id, invitee)
```
##### Reasoning
This service holds all the necessary invites data. It uses event id and invitee as a primary key so that each user can only be invited once to an event. When this service fails a user can't create a new event and won't see their invitations in the Invites tab. Private events will default to not showing to the user since we can't check if the user is invited. You can still see public events.
#### Calendars
##### Features
- PUT ``/share`` implements sharing your calendar with someone in the Share Calendar tab
- GET ``/calendars`` retrieving the calendar of a user, this is used to check if the calendar has been shared with you when you try to retrieve it.
##### Data
```sql
owner VARCHAR(100) PRIMARY KEY,
shared_with VARCHAR(100)[] NOT NULL
```
##### Reasoning
This service keeps track of whose calendars are shared with who, it is a one way relationship. When this service fails you'll default to not being able to access shared calendars, since we can't check if it is shared.
### Conclusion
This decomposition of microservices is scalable, because each microservice has its own concerns. It minimizes inter-service dependencies. Allowing for the other services to stay functional if one service is overloaded.
## API Documentation (Swagger)
| Service     | Location                    |
| ----------- | --------------------------- |
| GUI         | http://localhost:5001/docs/ |
| auth        | http://localhost:5002/docs/ |
| events      | http://localhost:5003/docs/ |
| invitations | http://localhost:5004/docs/ |
| calendars   | http://localhost:5005/docs/ |
