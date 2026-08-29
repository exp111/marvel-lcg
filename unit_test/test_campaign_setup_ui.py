from pathlib import Path
import unittest


class TestCampaignSetupUI(unittest.TestCase):

    def test_player_campaign_rows_update_without_regeneration(self):
        html = (
            Path(__file__).resolve().parents[1] / "public" / "scene.html"
        ).read_text(encoding="utf-8")

        self.assertIn("function updateCampaignPlayerRows()", html)
        self.assertIn("row.dataset.playerNumber = playerNumber", html)
        self.assertIn("row.hidden = parseInt(row.dataset.playerNumber) > visiblePlayers", html)
        self.assertIn("SetHero(j, i)", html)
        self.assertGreaterEqual(html.count("updateCampaignPlayerRows()"), 3)

    def test_required_encounter_set_buttons_cannot_be_deselected(self):
        html = (
            Path(__file__).resolve().parents[1] / "public" / "scene.html"
        ).read_text(encoding="utf-8")

        self.assertIn("if( div.classList.contains('lock') )", html)

    def test_campaign_settings_are_loaded_and_evidence_seed_can_be_randomized(self):
        html = (
            Path(__file__).resolve().parents[1] / "public" / "scene.html"
        ).read_text(encoding="utf-8")

        self.assertIn("fetchFresh('get_campaign_settings')", html)
        self.assertIn("function applyCampaignSettings(campaign_id, container)", html)
        self.assertIn("function randomizeCampaignNumber(button)", html)
        self.assertIn('onclick="randomizeCampaignNumber(this)"', html)
        self.assertIn('description: "Evidence Seed"', html)
        self.assertIn('label: "Evidence Seed (Do Not Change During a Campaign)"', html)

    def test_campaign_log_can_be_saved_without_starting_a_game(self):
        html = (
            Path(__file__).resolve().parents[1] / "public" / "scene.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="save_campaign_log_button"', html)
        self.assertIn("async function saveCampaignSettings(button)", html)
        self.assertIn("fetch('save_campaign_settings'", html)
        self.assertIn("campaign_log: readCampaignLog(campaign_id)", html)
        self.assertIn("new_game.campaign_log = readCampaignLog(selected_campaign_id)", html)

    def test_selected_campaign_can_be_cleared_with_confirmation(self):
        html = (
            Path(__file__).resolve().parents[1] / "public" / "scene.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="clear_campaign_log_button"', html)
        self.assertIn("async function clearCampaignSettings(button)", html)
        self.assertIn("window.confirm(", html)
        self.assertIn("fetch('clear_campaign_settings'", html)
        self.assertIn("body: JSON.stringify({ campaign_id })", html)
        self.assertIn('generateInputs("")', html)
        self.assertIn("Campaign log cleared.", html)

    def test_next_evolution_damage_destination_is_chosen_during_setup(self):
        html = (
            Path(__file__).resolve().parents[1] / "public" / "scene.html"
        ).read_text(encoding="utf-8")

        self.assertNotIn("Scenario 4 Hope Damage Placement", html)
        self.assertNotIn("Scenario 5 Hope Damage Placement", html)

    def test_mutant_genesis_defeated_schemes_can_be_deselected(self):
        html = (
            Path(__file__).resolve().parents[1] / "public" / "scene.html"
        ).read_text(encoding="utf-8")

        for description in (
            "Frightened Police Defeated",
            "Enemy of My Enemy Defeated",
            "Find the Prisoners Defeated",
            "Surprise Attack Defeated",
        ):
            self.assertIn(
                f'{{ description: "{description}", type: "checkbox", options: ["Yes"] }}',
                html,
            )
            self.assertNotIn(
                f'{{ description: "{description}", type: "select", options: ["Yes"] }}',
                html,
            )


if __name__ == "__main__":
    unittest.main()
