from generator.generation.catalog import TaxiCatalog


def test_catalog_creates_related_users_and_drivers() -> None:
    catalog = TaxiCatalog(
        cities=["Moscow", "Kazan"],
        tariffs=["economy", "comfort"],
        weather_types=["clear", "rain"],
        user_count=20,
        seed=7,
    )

    users = catalog.users()
    drivers = catalog.drivers()

    assert len(users) == 20
    assert drivers
    assert all(driver.is_taxist for driver in drivers)
    assert {driver.id for driver in drivers} <= {user.id for user in users}


def test_catalog_is_reproducible_with_seed() -> None:
    settings = {
        "cities": ["Moscow", "Kazan"],
        "tariffs": ["economy", "comfort"],
        "weather_types": ["clear", "rain"],
        "user_count": 20,
        "seed": 11,
    }
    first = TaxiCatalog(**settings)
    second = TaxiCatalog(**settings)

    assert first.users() == second.users()
    assert first.routes() == second.routes()
    assert [first.random_tarif() for _ in range(5)] == [second.random_tarif() for _ in range(5)]


def test_routes_have_positive_distance() -> None:
    catalog = TaxiCatalog(["Moscow"], ["economy"], ["clear"], user_count=10)

    assert catalog.routes()
    assert all(route.distance > 0 for route in catalog.routes())
    assert all(route.start_point != route.end_point for route in catalog.routes())
