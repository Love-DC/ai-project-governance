extends SceneTree

const CalendarHud = preload("res://scripts/calendar_hud.gd")


func _initialize() -> void:
    if not CalendarHud._validate_calendar_boundaries():
        push_error("Standalone calendar boundary validation failed.")
        quit(1)
        return

    print("UNBROKEN_FRONTIER_CALENDAR_STANDALONE_TEST_OK")
    quit(0)
