# GENERATED from the API specification. Do not edit.
TOOL_TEMPLATES = [
    {
        "id": "check_availability",
        "version": 1,
        "title": "Check availability",
        "category": "Bookings",
        "tool": {
            "type": "function",
            "name": "check_availability",
            "x-effect": "read",
            "description": (
                "Free appointment times on one day. Call it before offering any time; "
                "never guess times."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": (
                            "The day to check, as YYYY-MM-DD. Work out words like tomorrow from "
                            "today's date."
                        ),
                        "x-date": "booking",
                    },
                    "service": {
                        "type": "string",
                        "description": "The appointment type, if the caller named one.",
                    },
                    "staff": {
                        "type": "string",
                        "description": "The doctor or staff member the caller asked for, if any.",
                    },
                },
                "required": [
                    "date",
                ],
            },
        },
        "wiring": (
            "Look up open slots for that day in your calendar or booking system, "
            "narrowed by service and staff when given. Return the free start times as "
            "HH:MM, a handful at most, and an empty list when the day is full."
        ),
        "example": {
            "arguments": {
                "date": "2026-11-03",
            },
            "output": {
                "date": "2026-11-03",
                "slots": [
                    "10:00",
                    "11:30",
                    "15:00",
                ],
            },
        },
    },
    {
        "id": "book_appointment",
        "version": 1,
        "title": "Book appointment",
        "category": "Bookings",
        "tool": {
            "type": "function",
            "name": "book_appointment",
            "x-effect": "write",
            "description": (
                "Book an appointment at a time the caller chose. Use only a time "
                "check_availability returned."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": "The day, as YYYY-MM-DD.",
                    },
                    "time": {
                        "type": "string",
                        "format": "time",
                        "description": "The start time as HH:MM (24-hour), one check_availability returned.",
                    },
                    "name": {
                        "type": "string",
                        "description": "The caller's full name as they gave it.",
                    },
                    "phone": {
                        "type": "string",
                        "format": "phone",
                        "description": "The caller's mobile number.",
                    },
                    "service": {
                        "type": "string",
                        "description": "The appointment type, if the caller named one.",
                    },
                    "notes": {
                        "type": "string",
                        "x-free-text": True,
                        "description": "Anything else the caller wants the team to know.",
                    },
                },
                "required": [
                    "date",
                    "time",
                    "name",
                    "phone",
                ],
            },
        },
        "wiring": (
            "Create the booking in your system, re-checking that the slot is still "
            "free. Return the booking reference; if the slot was taken meanwhile, "
            "return an error with the next free times so the agent can offer them."
        ),
        "example": {
            "arguments": {
                "date": "2026-11-03",
                "time": "11:30",
                "name": "Tan Mei Ling",
                "phone": "+6591234567",
            },
            "output": {
                "status": "booked",
                "booking_id": "BK-0001",
                "date": "2026-11-03",
                "time": "11:30",
            },
        },
    },
    {
        "id": "reschedule_appointment",
        "version": 1,
        "title": "Reschedule appointment",
        "category": "Bookings",
        "tool": {
            "type": "function",
            "name": "reschedule_appointment",
            "x-effect": "write",
            "description": (
                "Move an existing booking to a new day and time the caller chose from "
                "check_availability."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": (
                            "The booking reference, from lookup_booking or as the caller reads it "
                            "out."
                        ),
                    },
                    "new_date": {
                        "type": "string",
                        "format": "date",
                        "description": "The new day, as YYYY-MM-DD.",
                    },
                    "new_time": {
                        "type": "string",
                        "format": "time",
                        "description": "The new start time as HH:MM (24-hour).",
                    },
                },
                "required": [
                    "booking_id",
                    "new_date",
                    "new_time",
                ],
            },
        },
        "wiring": (
            "Move the booking in your system in one step, so the caller never loses "
            "the old slot before the new one is held. Return the updated booking, or "
            "an error naming why it could not move."
        ),
        "example": {
            "arguments": {
                "booking_id": "BK-0001",
                "new_date": "2026-11-04",
                "new_time": "15:00",
            },
            "output": {
                "status": "rescheduled",
                "booking_id": "BK-0001",
                "date": "2026-11-04",
                "time": "15:00",
            },
        },
    },
    {
        "id": "cancel_appointment",
        "version": 1,
        "title": "Cancel appointment",
        "category": "Bookings",
        "tool": {
            "type": "function",
            "name": "cancel_appointment",
            "x-effect": "write",
            "description": "Cancel an existing booking after the caller confirmed which one.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": (
                            "The booking reference, from lookup_booking or as the caller reads it "
                            "out."
                        ),
                    },
                    "reason": {
                        "type": "string",
                        "x-free-text": True,
                        "description": "Why the caller is cancelling, if they said.",
                    },
                },
                "required": [
                    "booking_id",
                ],
            },
        },
        "wiring": (
            "Cancel the booking in your system and free the slot. Return the "
            "cancelled booking; apply your own late-cancellation rules and return "
            "them as a message the agent can read out."
        ),
        "example": {
            "arguments": {
                "booking_id": "BK-0001",
            },
            "output": {
                "status": "cancelled",
                "booking_id": "BK-0001",
            },
        },
    },
    {
        "id": "lookup_booking",
        "version": 1,
        "title": "Look up a booking",
        "category": "Bookings",
        "tool": {
            "type": "function",
            "name": "lookup_booking",
            "x-effect": "read",
            "description": (
                "Find the caller's upcoming bookings by phone number or booking "
                "reference. Give at least one of them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "format": "phone",
                        "description": "The mobile number the booking was made with.",
                    },
                    "booking_id": {
                        "type": "string",
                        "description": "The booking reference, if the caller has it.",
                    },
                },
                "required": [],
            },
        },
        "wiring": (
            "Search upcoming bookings by phone or reference. Return only bookings "
            "that phone or reference owns, never anyone else's, with the reference, "
            "day, time and service of each."
        ),
        "example": {
            "arguments": {
                "phone": "+6591234567",
            },
            "output": {
                "bookings": [
                    {
                        "booking_id": "BK-0001",
                        "date": "2026-11-03",
                        "time": "11:30",
                        "service": "General consultation",
                    },
                ],
            },
        },
    },
    {
        "id": "opening_hours",
        "version": 1,
        "title": "Opening hours",
        "category": "Information",
        "tool": {
            "type": "function",
            "name": "opening_hours",
            "x-effect": "read",
            "description": (
                "Opening hours, including public holidays. Call it when the caller asks "
                "when you are open."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": (
                            "A specific day to check, as YYYY-MM-DD. Leave it out for the usual "
                            "weekly hours."
                        ),
                    },
                    "location": {
                        "type": "string",
                        "description": "The branch, if you have more than one.",
                    },
                },
                "required": [],
            },
        },
        "wiring": (
            "Return the weekly hours as one short sentence, or that day's hours when "
            "a date is given, with any holiday closure."
        ),
        "example": {
            "arguments": {},
            "output": {
                "hours": "Monday to Friday 8:30 am to 9 pm and Saturday 8:30 am to 1 pm",
            },
        },
    },
    {
        "id": "geocode",
        "version": 1,
        "title": "Look up an address",
        "category": "Location",
        "tool": {
            "type": "function",
            "name": "geocode",
            "x-effect": "read",
            "description": (
                "Turn a place the caller named (address, postal code, building or "
                "landmark) into a full address and map coordinates. Call it before "
                "ranking branches or checking the service area."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The place as the caller said it, for example a street and block number, "
                            "a postal code or a landmark."
                        ),
                    },
                    "country": {
                        "type": "string",
                        "pattern": "^[A-Z]{2}$",
                        "description": (
                            "The two-letter country code to search in, for example SG. Leave it out "
                            "for the business's own country."
                        ),
                    },
                },
                "required": [
                    "query",
                ],
            },
        },
        "wiring": (
            "Look the place up in your address or map service, limited to your "
            "country. Return the best match's full address, postal code and "
            "coordinates; when the match is unsure, add up to three other matches so "
            "the agent can ask which one."
        ),
        "example": {
            "arguments": {
                "query": "Tampines Central 1",
            },
            "output": {
                "address": "10 Tampines Central 1, Singapore 529536",
                "postal_code": "529536",
                "latitude": 1.3532,
                "longitude": 103.9452,
                "confidence": "high",
            },
        },
    },
    {
        "id": "find_nearest_branch",
        "version": 1,
        "title": "Find nearest branch by travel time",
        "category": "Location",
        "tool": {
            "type": "function",
            "name": "find_nearest_branch",
            "x-effect": "read",
            "description": (
                "Rank the business's branches by travel time from the caller, for the way "
                "they will travel. Give origin, or latitude and longitude from geocode."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": (
                            "Where the caller is starting from: an address, postal code, area, "
                            "landmark or station."
                        ),
                    },
                    "latitude": {
                        "type": "number",
                        "minimum": -90,
                        "maximum": 90,
                        "description": "The caller's latitude, when geocode already returned it.",
                    },
                    "longitude": {
                        "type": "number",
                        "minimum": -180,
                        "maximum": 180,
                        "description": "The caller's longitude, when geocode already returned it.",
                    },
                    "mode": {
                        "type": "string",
                        "enum": [
                            "transit",
                            "driving",
                            "walking",
                            "cycling",
                        ],
                        "description": "How the caller will travel. Leave it out for public transport.",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "How many branches to return, nearest first. Leave it out for three.",
                    },
                },
                "required": [],
            },
        },
        "wiring": (
            "Ask your routing service for the travel time from the caller's place to "
            "each branch by that mode, and sort by it, never by straight-line "
            "distance. Return each branch's name, address, minutes and a one-line "
            "route summary."
        ),
        "example": {
            "arguments": {
                "origin": "Pasir Ris Drive 3",
                "mode": "transit",
            },
            "output": {
                "mode": "transit",
                "branches": [
                    {
                        "branch": "Tampines",
                        "address": "10 Tampines Central 1, #02-15",
                        "travel_minutes": 14,
                        "summary": "Bus 3 to Tampines station, then two minutes' walk.",
                    },
                    {
                        "branch": "Bedok",
                        "address": "311 New Upper Changi Road, #01-20",
                        "travel_minutes": 27,
                        "summary": "Train from Pasir Ris to Bedok, exit B.",
                    },
                ],
            },
        },
    },
    {
        "id": "get_directions",
        "version": 1,
        "title": "Directions to a branch",
        "category": "Location",
        "tool": {
            "type": "function",
            "name": "get_directions",
            "x-effect": "read",
            "description": (
                "Step-by-step directions from the caller's place to one branch, by the "
                "way they will travel. Call it when the caller asks how to get there."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": (
                            "Where the caller is starting from: an address, postal code, area, "
                            "landmark or station."
                        ),
                    },
                    "branch": {
                        "type": "string",
                        "description": (
                            "The branch to go to, by the name find_nearest_branch returned or the "
                            "caller gave."
                        ),
                    },
                    "mode": {
                        "type": "string",
                        "enum": [
                            "transit",
                            "driving",
                            "walking",
                            "cycling",
                        ],
                        "description": "How the caller will travel. Leave it out for public transport.",
                    },
                },
                "required": [
                    "origin",
                    "branch",
                ],
            },
        },
        "wiring": (
            "Ask your routing service for a route from the origin to the branch "
            "entrance by that mode. Return the minutes, a one-sentence summary and at "
            "most five short steps the agent can read out, never only a map link."
        ),
        "example": {
            "arguments": {
                "origin": "Pasir Ris Drive 3",
                "branch": "Tampines",
                "mode": "transit",
            },
            "output": {
                "branch": "Tampines",
                "mode": "transit",
                "travel_minutes": 14,
                "summary": "Bus 3 to Tampines station, then a short walk.",
                "steps": [
                    "Walk to the bus stop outside Block 440.",
                    "Take bus 3 for six stops to Tampines station.",
                    "Leave by exit A and walk two minutes to 10 Tampines Central 1, level 2.",
                ],
            },
        },
    },
    {
        "id": "check_service_area",
        "version": 1,
        "title": "Check service area",
        "category": "Location",
        "tool": {
            "type": "function",
            "name": "check_service_area",
            "x-effect": "read",
            "description": (
                "Whether an address or postal code is inside the area the business "
                "serves, for home visits, deliveries or on-site jobs. Call it before "
                "offering a visit to the caller's address."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "The caller's address or postal code, as they gave it.",
                    },
                    "service": {
                        "type": "string",
                        "description": "The service the caller wants, if your area differs by service.",
                    },
                },
                "required": [
                    "address",
                ],
            },
        },
        "wiring": (
            "Match the address to your service area (a postal-code list or a map "
            "boundary). Return whether it is inside, the area's name, and when it is "
            "outside a short message the agent can read out, such as the nearest area "
            "you do cover."
        ),
        "example": {
            "arguments": {
                "address": "529536",
            },
            "output": {
                "in_area": True,
                "area": "East",
            },
        },
    },
    {
        "id": "order_status",
        "version": 1,
        "title": "Order status",
        "category": "Orders",
        "tool": {
            "type": "function",
            "name": "order_status",
            "x-effect": "read",
            "description": (
                "Where an order is and when it should arrive. Ask for the order number "
                "first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order number as the caller reads it out, for example A1042.",
                    },
                },
                "required": [
                    "order_id",
                ],
            },
        },
        "wiring": (
            "Look the order up in your order system. Return its status in plain words "
            "and the delivery estimate; for an unknown number, return an error so the "
            "agent asks again."
        ),
        "example": {
            "arguments": {
                "order_id": "A1042",
            },
            "output": {
                "order_id": "A1042",
                "status": "out for delivery",
                "eta": "today before 6 pm",
            },
        },
    },
    {
        "id": "check_stock",
        "version": 1,
        "title": "Check stock",
        "category": "Orders",
        "tool": {
            "type": "function",
            "name": "check_stock",
            "x-effect": "read",
            "description": "Whether a product is in stock, and how many are left.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "The product name or model the caller asked about.",
                    },
                    "location": {
                        "type": "string",
                        "description": "The store to check, if you have more than one.",
                    },
                },
                "required": [
                    "item",
                ],
            },
        },
        "wiring": (
            "Match the item to your catalogue and return whether it is in stock and "
            "the count. When the match is unsure, return the closest products so the "
            "agent can ask which one."
        ),
        "example": {
            "arguments": {
                "item": "8 kg washing machine",
            },
            "output": {
                "item": "8 kg washing machine",
                "in_stock": True,
                "quantity": 12,
            },
        },
    },
    {
        "id": "transfer_to_staff",
        "version": 1,
        "title": "Transfer to staff",
        "category": "Handoff",
        "tool": {
            "type": "function",
            "name": "transfer_to_staff",
            "x-effect": "write",
            "description": (
                "Hand the call to a person when the caller asks for one or the request is "
                "outside your tools."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "team": {
                        "type": "string",
                        "enum": [
                            "front_desk",
                            "billing",
                            "support",
                        ],
                        "description": "Which team should take the call. Edit this list to your own teams.",
                    },
                    "reason": {
                        "type": "string",
                        "x-free-text": True,
                        "description": "One line on what the caller needs, so staff pick up with context.",
                    },
                },
                "required": [
                    "team",
                ],
            },
        },
        "wiring": (
            "Start the transfer in your phone system and return its status. Out of "
            "hours or when nobody answers, return that status so the agent offers "
            "take_message instead."
        ),
        "example": {
            "arguments": {
                "team": "billing",
                "reason": "Question about an invoice",
            },
            "output": {
                "status": "transferring",
                "team": "billing",
            },
        },
    },
    {
        "id": "take_message",
        "version": 1,
        "title": "Take a message",
        "category": "Handoff",
        "tool": {
            "type": "function",
            "name": "take_message",
            "x-effect": "write",
            "description": "Leave a message for the team to call the caller back.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The caller's name.",
                    },
                    "phone": {
                        "type": "string",
                        "format": "phone",
                        "description": "The number to call back.",
                    },
                    "message": {
                        "type": "string",
                        "x-free-text": True,
                        "description": "What the caller wants, in their words.",
                    },
                    "callback_window": {
                        "type": "string",
                        "enum": [
                            "morning",
                            "afternoon",
                            "evening",
                            "any",
                        ],
                        "description": "When the caller prefers a call back.",
                    },
                },
                "required": [
                    "name",
                    "phone",
                    "message",
                ],
            },
        },
        "wiring": (
            "Save the message where your team works (inbox, ticket or chat) and "
            "return its reference."
        ),
        "example": {
            "arguments": {
                "name": "Tan Mei Ling",
                "phone": "+6591234567",
                "message": "Please call about my test results.",
                "callback_window": "afternoon",
            },
            "output": {
                "status": "saved",
                "message_id": "MSG-0001",
            },
        },
    },
    {
        "id": "send_confirmation",
        "version": 1,
        "title": "Send confirmation",
        "category": "Handoff",
        "tool": {
            "type": "function",
            "name": "send_confirmation",
            "x-effect": "write",
            "description": (
                "Send the caller the details of a booking or order by text message or "
                "email."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reference": {
                        "type": "string",
                        "description": "The booking or order reference to confirm.",
                    },
                    "channel": {
                        "type": "string",
                        "enum": [
                            "sms",
                            "email",
                        ],
                        "description": "How to send it.",
                    },
                },
                "required": [
                    "reference",
                    "channel",
                ],
            },
        },
        "wiring": (
            "Send to the contact already on the booking or order, never to a number "
            "or address read out on the call, and return whether it went out."
        ),
        "example": {
            "arguments": {
                "reference": "BK-0001",
                "channel": "sms",
            },
            "output": {
                "status": "sent",
                "channel": "sms",
            },
        },
    },
]

TOOL_CHECKER = {
    "rules": {
        "tool_invalid": "error",
        "name_invalid": "error",
        "name_reserved": "error",
        "name_duplicate": "error",
        "effect_invalid": "error",
        "action_invalid": "error",
        "parameters_invalid": "error",
        "schema_too_large": "error",
        "pattern_invalid": "error",
        "patterns_too_many": "error",
        "tools_too_many": "error",
        "effect_missing": "warning",
        "effect_read_looks_like_write": "warning",
        "action_on_read": "warning",
        "description_missing": "warning",
        "description_vague": "warning",
        "param_description_missing": "warning",
        "format_missing": "warning",
        "format_unknown": "warning",
        "coordinates_unbounded": "warning",
        "required_unknown": "warning",
        "near_duplicate": "warning",
        "tools_many": "warning",
    },
    "accuracyTools": 8,
    "minDescriptionBytes": 20,
    "similarity": {
        "name": 0.85,
        "description": 0.7,
    },
    "formats": [
        "date",
        "date-time",
        "time",
        "email",
        "phone",
        "tel",
    ],
    "writeHints": [
        "add",
        "book",
        "buy",
        "cancel",
        "change",
        "charge",
        "create",
        "delete",
        "edit",
        "pay",
        "purchase",
        "refund",
        "register",
        "remove",
        "reschedule",
        "reserve",
        "save",
        "send",
        "set",
        "submit",
        "subscribe",
        "transfer",
        "unsubscribe",
        "update",
    ],
    "formatHints": {
        "date": [
            "date",
            "day",
            "dob",
            "birthday",
            "birthdate",
        ],
        "time": [
            "time",
            "hour",
        ],
        "date-time": [
            "datetime",
            "timestamp",
        ],
        "phone": [
            "phone",
            "mobile",
            "tel",
            "telephone",
        ],
    },
    "coordinateHints": {
        "latitude": {
            "words": [
                "lat",
                "latitude",
            ],
            "minimum": -90,
            "maximum": 90,
        },
        "longitude": {
            "words": [
                "lng",
                "lon",
                "longitude",
            ],
            "minimum": -180,
            "maximum": 180,
        },
    },
}
