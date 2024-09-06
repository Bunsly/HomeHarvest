_SEARCH_HOMES_DATA_BASE = """{
    pending_date
    listing_id
    property_id
    href
    list_date
    status
    last_sold_price
    last_sold_date
    list_price
    list_price_max
    list_price_min
    price_per_sqft
    flags {
        is_contingent
        is_pending
        is_new_construction
    }
    description {
        type
        sqft
        beds
        baths_full
        baths_half
        lot_sqft
        year_built
        garage
        type
        name
        stories
        text
    }
    source {
        id
        listing_id
    }
    hoa {
        fee
    }
    location {
        address {
            street_direction
            street_number
            street_name
            street_suffix
            line
            unit
            city
            state_code
            postal_code
            coordinate {
                lon
                lat
            }
        }
        county {
            name
            fips_code
        }
        neighborhoods {
            name
        }
    }
    tax_record {
        public_record_id
    }
    primary_photo {
        href
    }
    photos {
        href
    }
    advertisers {
        email
        broker {
            name
            fulfillment_id
        }
        type
        name
        fulfillment_id
        builder {
            name
            fulfillment_id
        }
        phones {
            ext
            primary
            type
            number
        }
        office {
            name
            email
            fulfillment_id
            href
            phones {
                number
                type
                primary
                ext
            }
            mls_set
        }
        corporation {
            specialties
            name
            bio
            href
            fulfillment_id
        }
        mls_set
        nrds_id
        rental_corporation {
            fulfillment_id
        }
        rental_management {
            name
            fulfillment_id
        }
    }
    """

HOMES_DATA = """%s
                nearbySchools: nearby_schools(radius: 5.0, limit_per_level: 3) {
                            __typename schools { district { __typename id name } }
                        }
                taxHistory: tax_history { __typename tax year assessment { __typename building land total } }
                estimates {
                    __typename
                    currentValues: current_values {
                        __typename
                        source { __typename type name }
                        estimate
                        estimateHigh: estimate_high
                        estimateLow: estimate_low
                        date
                        isBestHomeValue: isbest_homevalue
                    }
                }
}""" % _SEARCH_HOMES_DATA_BASE

SEARCH_HOMES_DATA = """%s
                    current_estimates {
                            __typename
                            source {
                                __typename
                                type
                                name
                            }
                            estimate
                            estimateHigh: estimate_high
                            estimateLow: estimate_low
                            date
                            isBestHomeValue: isbest_homevalue
                        }
}""" % _SEARCH_HOMES_DATA_BASE

GENERAL_RESULTS_QUERY = """{
                            count
                            total
                            results %s
                        }""" % SEARCH_HOMES_DATA
