from src.core.category_manager import CategoryManager
from src.core.organization_profiles import ProfileManager


def test_category_manager_can_update_and_toggle_custom_rules(tmp_path):
    config_path = tmp_path / "categories.json"
    manager = CategoryManager(str(config_path))

    assert manager.add_custom_rule("Docs", "regex:.*invoice.*", "DOCUMENTOS", 40)
    assert len(manager.get_custom_rules()) == 1

    assert manager.update_custom_rule(
        "Docs",
        name="Docs prioritarios",
        pattern="invoice",
        category="DOCUMENTOS",
        priority=80,
        enabled=False,
    )

    rule = manager.get_custom_rules()[0]
    assert rule.name == "Docs prioritarios"
    assert rule.pattern == "invoice"
    assert rule.priority == 80
    assert rule.enabled is False

    assert manager.toggle_custom_rule("Docs prioritarios") is True
    assert manager.get_custom_rules()[0].enabled is True


def test_profile_manager_persists_custom_profile_changes(tmp_path):
    profiles_path = tmp_path / "profiles.json"
    manager = ProfileManager(str(profiles_path))

    profile = manager.create_profile("Descargas", "Perfil para carpeta de descargas")
    profile.folder_path = "/tmp/downloads"
    profile.move_folders = False
    profile.similarity_threshold = 85
    profile.organize_by_date = True
    profile.selected_categories = ["DOCUMENTOS", "PROGRAMAS"]

    assert manager.update_profile(profile) is True
    assert manager.set_active_profile("Descargas") is True

    reloaded = ProfileManager(str(profiles_path))
    loaded_profile = reloaded.get_profile("Descargas")
    assert loaded_profile is not None
    assert loaded_profile.folder_path == "/tmp/downloads"
    assert loaded_profile.move_folders is False
    assert loaded_profile.similarity_threshold == 85
    assert loaded_profile.organize_by_date is True
    assert loaded_profile.selected_categories == ["DOCUMENTOS", "PROGRAMAS"]
    assert reloaded.get_active_profile().name == "Descargas"
