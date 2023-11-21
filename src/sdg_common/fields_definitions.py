class Field:
    def __init__(self, field_id, faker_method, display, data_type, example):
        self.field_id = field_id
        self.faker_method = faker_method
        self.display = display
        self.data_type = data_type
        self.example = example


field_definitions = {
    "first_name": Field('first_name', 'first_name', 'First Name', str, 'Vasile'),
    "last_name": Field('last_name', 'last_name', 'Last Name', str, 'Popescu'),
    "personal_number": Field('personal_number', 'ssn', 'Social Personal Number', int, '8240804276204'),
    "birthdate": Field('birthdate', 'date_of_birth', 'Date', 'date', '2023-04-19'),
    "address": Field('address', 'address', 'Address with Postcode', str, 'Intrarea Nr. 167 Nicolau Mare, 197205'),
    "county": Field('county', 'state', 'County Name', str, 'Hunedoara'),
    "phone_number": Field('phone_number', 'phone_number', 'Phone Number', str, '0248 455 730'),
    "mac_address": Field('mac_address', 'mac_address', 'MAC Address', str, 'd4:a3:82:98:85:a6'),
    "ip_address": Field('ip_address', 'ipv4', 'IP Address', str, '172.25.185.30'),
    "job": Field('job', 'job', 'Job Title', str, 'Pictor'),
    "iban": Field('iban', 'iban', 'Bank Account Number', str, 'RO83YUNU3862659030037214'),
    "currency": Field('currency', 'currency_code', 'Currency Code', str, 'XAF'),
    "balance": Field('balance', 'random_number', 'Random Number', int, '75564642'),
    "latitude": Field('latitude', 'latitude', 'Latitude Value', float, '27.6863225'),
    "longitude": Field('longitude', 'longitude', 'Longitude Value', float, '44.431989')
}
