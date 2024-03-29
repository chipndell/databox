import re
import os
import random
import hashlib
from .gen_response import InvalidURL

from functools import reduce
from flask import g

from werkzeug.exceptions import Locked

CAPITAL_LETTERS = (65, 90)
SMALL_CAP_LETTERS = (96, 122)
STREET_NAME_SET = (
    "Parkcrest Drive",
    "Acland Crescent",
    "Annis Road",
    "Beare Road",
    "Bell Estate Road",
    "Bellamy Road",
    "Bennett Road",
    "Berner Trail",
    "Bethune Boulevard",
    "Birchcliff Avenue",
    "Blantyre Avenue",
    "Boem Avenue",
    "Bonis Avenue",
    "Borough Drive",
    "Bridlewood Boulevard ",
    " Bridletown Circle",
    "Brumwell Street",
    "Byng Avenue",
    "Cathedral Bluffs Drive",
    "Cecil Crescent",
    "Centennial Road",
    "Civic Road",
    "Closson Drive",
    "Colonel Danforth Trail",
    "Comrie Terrace",
    "Conlins Road",
    "Conn Smythe Drive",
    "Cornell Avenue",
    "Crockford Boulevard",
    "Reeve Crockford",
    "Dairy Drive",
    "Denton Ave",
    "Ellesmere Road",
    "Empringham Drive",
    "Falcon Lane",
    "Fallingbrook Road",
    "Frank Faubert Drive",
    "Galloway Road",
    "Glen Muir Drive",
    "Glendinning Avenue",
    "Glenshephard Drive",
    "Gooderham Drive",
    "Haig Avenue",
    "Harrisfarm Gate",
    "Heather Road",
    "Iondale Place",
    "Ionview Road",
    "Jean Dempsey Gate",
    "John Stoner Drive",
    "John Tabor Trail",
    "Kingston Road",
    "Kalmar Avenue",
    "Kelvin Grove Avenue",
    "Kennedy Road",
    "Ketchum Place",
    "Kingsbury Crescent",
    "Knowles Drive",
    "Macklingate Court",
    "Mammoth Hall Trail",
    "Manse Road",
    "Manville Road",
    "Markham Road",
    "McCowan Road",
    "Midland Avenue",
    "Mike Myers Drive",
    "Milne Avenue",
    "Milliken Boulevard",
    "Morrish Road",
    "Neilson Avenue",
    "Neilson Road",
    "Ormerod Street",
    "Orton Park Road",
    "Osterhout Place",
    "Painted Post Drive",
    "Parkcrest Drive",
    "Passmore Avenue ",
    "Patterson Avenue",
    "Pilkington Drive",
    "Port Union Road",
    "Park Street",
    "Purcell Square",
    "Reesor Road",
    "Rhydwen Avenue",
    "Rouge Hills Drive",
    "Sandown Avenue",
    "Scarboro Crescent",
    "Scarborough Heights Boulevard",
    "Sewells Road",
    "Stobo Lane",
    "Tollgate Mews",
    "Torrance Road",
    "Thermos Road",
    "Underwriters Road",
    "Victoria Park Avenue",
    "Walbon Road",
    "Warden Avenue",
    "Wayne Avenue",
    "Wexford Boulevard",
    "William Kitchen Road",
)

CITY_NAME_SET = (
    "Stockton",
    "Chula Vista",
    "Irvine",
    "Fremont",
    "San Bernardino",
    "Modesto",
    "Fontana",
    "Oxnard",
    "Moreno Valley",
    "Huntington Beach",
    "Glendale",
    "Santa Clarita",
    "Garden Grove",
    "Oceanside",
    "Rancho Cucamonga",
    "Santa Rosa",
    "Ontario",
    "Lancaster",
    "Elk Grove",
    "Corona",
    "Palmdale",
    "Salinas",
    "Pomona",
    "Hayward",
    "Escondido",
    "Torrance",
    "Sunnyvale",
    "Orange",
    "Fullerton",
    "Pasadena",
    "Thousand Oaks",
    "Visalia",
    "Simi Valley",
    "Concord",
    "Roseville",
    "Victorville",
    "Santa Clara",
    "Vallejo",
    "Berkeley",
    "El Monte",
    "Downey",
    "Costa Mesa",
    "Inglewood",
    "Carlsbad",
    "San Buenaventura (Ventura)",
    "Fairfield",
    "West Covina",
    "Murrieta",
    "Richmond",
    "Norwalk",
    "Antioch",
    "Temecula",
    "Burbank",
    "Daly City",
    "Rialto",
    "Santa Maria",
    "El Cajon",
    "San Mateo",
    "Clovis",
    "Compton",
)

PROVINCE_SET = (
    "Ontario",
    "Quebec",
    "Nova Scotia",
    "New Brunswick",
    "Manitoba",
    "British Columbia",
    "Prince Edward Island",
    "Saskatchewan",
    "Alberta",
    "Newfoundland and Labrador",
    "Alabama",
    "Alaska",
    "American Samoa",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Commonwealth of the Northern Mariana Islands",
    "Connecticut",
    "Delaware",
    "District of Columbia",
    "Florida",
    "Georgia",
    "Guam",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Puerto Rico",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "United States Virgin Islands",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
)

EMAIL_SET = (
    "@icloud.com",
    "@gmail.com",
    "@yahoo.com",
    "@protonmail.com",
    "@live.com",
)

FIRST_NAME_SET = (
    "Luke",
    "James",
    "Sarah",
    "Cody",
    "Robert",
    "John",
    "Michael",
    "Thomas",
    "Aubrey",
    "Erin",
    "Riley",
    "Adam",
    "Lee",
    "Cecil",
    "Kaden",
    "Joseph",
    "Christopher",
    "Charles",
    "Daniel",
    "Matthew",
    "Mark",
    "Donald",
    "Steven",
    "Gary",
    "Eric",
    "Jonathan",
    "Stephen",
    "Larry",
    "Scott",
    "Brandon",
    "Jack",
)
LAST_NAME_SET = (
    "Skywalker",
    "Brown",
    "Tatum",
    "Gates",
    "Bezos",
    "Sandler",
    "Jones",
    "Johnson",
    "Smith",
    "Davis",
    "Rodriguez",
    "Lopez",
    "Hernandez",
    "Wilson",
    "Gonzalez",
    "Thomas",
    "Taylor",
    "Clark",
    "Lewiz",
    "White",
    "Clark",
    "Lewis",
    "Ramirez",
    "Hall",
    "Baker",
)

PHONE_SERIES = ("647", "514", "226", "705", "908", "512", "310", "702", "404")
TELE_SERIES = ("7", "2", "3")


def random_address_generator():
    street_no = str(random.randint(0, 5000))
    street_address = random.sample(STREET_NAME_SET, 1)[0] + " street"
    city = random.sample(CITY_NAME_SET, 1)[0]
    province = random.sample(PROVINCE_SET, 1)[0]
    temp_nums = random.sample(range(0, 9), 3)
    temp_letters = [chr(i) for i in random.sample(range(*CAPITAL_LETTERS), 3)]
    postal_code = ""
    for i in range(3):
        postal_code += temp_letters[i] + str(temp_nums[i])
    postal_code = postal_code[:3] + " " + postal_code[3:]
    address = (
        street_no
        + " "
        + ", ".join((street_address, city, province, postal_code))
        + " Canada"
    )
    return address


def random_user_generator():
    first_name = random.sample(FIRST_NAME_SET, 1)[0]
    last_name = random.sample(LAST_NAME_SET, 1)[0]
    age = random.randint(0, 125)
    phone = reduce(
        lambda a, b: a + str(b),
        random.sample(range(0, 9), 7),
        random.choice(PHONE_SERIES),
    )
    telephone = reduce(
        lambda a, b: a + str(b),
        random.sample(range(0, 9), 6),
        random.choice(TELE_SERIES),
    )
    address = random_address_generator()
    email = (
        first_name + "." + last_name + str(random.randint(0, 999))
    ).lower() + random.choice(EMAIL_SET)
    user = {
        "first_name": first_name,
        "last_name": last_name,
        "age": int(age),
        "address": address,
        "telephone": telephone,
        "phone": phone,
        "email": email,
    }
    return user


def create_hash_password(password):
    salt = os.environ["SALT"].encode()
    hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    key = (salt + hash).hex()
    return key


def check_password(password, hash_orig_password):
    if create_hash_password(password) == hash_orig_password:
        return True
    else:
        return False


def sw(value, pattern):
    try:
        if value.lower().startswith(pattern.lower()):
            return True
    except AttributeError:
        if str(value).startswith(str(pattern)):
            return True
    else:
        return False


def deprecated(message=""):
    def outerwrapper(func):
        def wrapper(*args, **kwargs):
            print(
                f"The `{func.__qualname__}` function will be deprecated soon. {message}"
            )
            return func(*args, **kwargs)

        return wrapper

    return outerwrapper


def is_users_content(func):
    def wrapper(*args, **kwargs):
        if kwargs["username"] == g.current_user.username:
            return func(*args, **kwargs)
        raise Locked

    return wrapper


def generic_open(filename, mode):
    try:
        return open(filename, mode=mode)
    except FileNotFoundError:
        raise InvalidURL


def _in(value, pattern):
    if pattern in value:
        return True
    else:
        return False


def username_type(username_str):
    if re.fullmatch("[a-z0-9]{5,10}", username_str):
        return username_str
    else:
        raise ValueError("Username has to be aplphanumeric and 5-10 chars long.")


def fields_type(fields_str):
    if re.fullmatch("([\w]{2,31}:(int|str|float),?)+", fields_str):
        return fields_str
    else:
        raise ValueError(
            "`fields` has to be in this form, `col_name:col_type,col_name1:"
            "col_type1,col_name2:col_type2`. Valid types are `int`,`str` and"
            " `float`"
        )


def email_type(email_str):
    if re.fullmatch("[a-z0-9.]{5,32}@[a-z]{3,32}.[a-z]{1,16}", email_str):
        return email_str
    else:
        raise ValueError(
            "Email is not valid!! It has to be `(5-32 alphanumeric letters)@(3-32 "
            "alphabet letters).(1-16 alphabet letters)`"
        )
