from homeharvest.utils import parse_address_one, parse_address_two


def test_parse_address_one():
    test_data = [
        ("4303 E Cactus Rd Apt 126", ("4303 E Cactus Rd", "#126")),
        ("1234 Elm Street apt 2B", ("1234 Elm Street", "#2B")),
        ("1234 Elm Street UNIT 3A", ("1234 Elm Street", "#3A")),
        ("1234 Elm Street unit 3A", ("1234 Elm Street", "#3A")),
        ("1234 Elm Street SuIte 3A", ("1234 Elm Street", "#3A")),
    ]

    for input_data, (exp_addr_one, exp_addr_two) in test_data:
        address_one, address_two = parse_address_one(input_data)
        assert address_one == exp_addr_one
        assert address_two == exp_addr_two


def test_parse_address_two():
    test_data = [("Apt 126", "#126"), ("apt 2B", "#2B"), ("UNIT 3A", "#3A"), ("unit 3A", "#3A"), ("SuIte 3A", "#3A")]

    for input_data, expected in test_data:
        output = parse_address_two(input_data)
        assert output == expected
