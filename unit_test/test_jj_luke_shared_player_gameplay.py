import unittest

from unit_test.jj_luke_gameplay_helpers import Gameplay


class TestSharedPlayerCards(Gameplay, unittest.TestCase):
    pack = "jj"

    def search(self, cid):
        def choose(prompt):
            options=[o for o in prompt.options if prompt.event_name == "WhenPlayerChooseAbility"
                     and o["is_search"] and o["name"] != "Resolve Mulligans"]
            if options: return self.descriptor(options[0],cid)
            return self.choices()(prompt)
        return choose

    def test_unbreakable_bond_both_printings_heal_three_to_one_character(self):
        for cid in ("61027","62024"):
            with self.subTest(cid=cid):
                s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("61003")',
                    'puzzle.Damage(hero,4)','puzzle.SetThreat("01097b",6)',
                    *self.hand(cid,"01088"),self.use(cid)])[-1]
                self.assertEqual(s["health"],10)
                self.assertEqual(s["main_threat"],3)
                self.assertEqual(s["hand"],[])

    def test_unbreakable_bond_distributes_healing_between_characters(self):
        def choose(prompt):
            options=[o for o in prompt.options if o["name"]=="Distribute_3_healing"]
            if options:
                hero=self.descriptor(options[0],"61001a").targets[0]
                ally=self.descriptor(options[0],"61003").targets[0]
                result=self.descriptor(options[0])
                result.targets=[hero,ally,hero]
                return result
            return NotImplemented
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("61003")',
            'puzzle.Damage("61003",1)','puzzle.Damage("61003",2)','puzzle.Damage(hero,4)',
            'puzzle.SetThreat("01097b",6)',*self.hand("61027","01088"),self.use("61027")],choose_other=choose)[-1]
        self.assertEqual(s["health"],9)
        self.assertEqual(self.face(s,"61003")["hp"],2)
        self.assertEqual(s["main_threat"],3)

    def test_unbreakable_bond_confused_replaces_entire_thwart_including_healing(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("61003")',
            'puzzle.Damage(hero,4)','puzzle.Confuse(hero)','puzzle.SetThreat("01097b",6)',
            *self.hand("61027","01088"),self.use("61027")])[-1]
        self.assertEqual(s["health"],7)
        self.assertEqual(s["main_threat"],6)
        self.assertFalse(s["confused"])
        self.assertEqual(s["hand"],[])

    def test_team_up_requires_both_named_characters_in_play(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")',*self.hand("61027","62023","01088")])[-1]
        self.assertFalse(any(cid in ("61027","62023") for cid,name in s["actions"]))

    def test_power_man_iron_fist_deals_damage_and_gives_chosen_character_tough(self):
        self.pack="luke_cage"
        for target in ("62012","62001a","01094"):
            with self.subTest(target=target):
                s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("62012")',
                    *self.hand("62023"),self.use("62023")],
                    choose_other=self.choices(names=("Give a character",),target=target))
                self.assertEqual(s[-2]["villain_health"]-s[-1]["villain_health"],2)
                self.assertEqual(self.face(s[-1],target)["tough"],1)

    def test_power_man_iron_fist_stun_replaces_entire_attack(self):
        self.pack="luke_cage"
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("62012")','puzzle.Stun(hero)',
            *self.hand("62023"),self.use("62023")],
            choose_other=self.choices(names=("Give a character",),target="62012"))
        self.assertEqual(s[-1]["villain_health"],s[-2]["villain_health"])
        self.assertEqual(self.face(s[-1],"62012")["tough"],0)
        self.assertFalse(s[-1]["stunned"])

    def test_dynamic_duo_finds_new_team_up_and_named_ally(self):
        self.pack="luke_cage"
        for from_discard in (False,True):
            with self.subTest(from_discard=from_discard):
                picks=iter(("62023","62012"))
                def choose(prompt):
                    options=[o for o in prompt.options if o["is_search"] and o["name"] != "Resolve Mulligans"]
                    if options: return self.descriptor(options[0],next(picks))
                    return NotImplemented
                s=self.play([*self.hand("62022","62025"),
                    'puzzle.CreatePlayer'+('DiscardPile' if from_discard else 'Deck')+'("62023","62012")',
                    self.use("62022")],choose_other=choose)[-1]
                self.assertCountEqual(s["hand"],["62023","62012"])

    def test_second_chance_shuffles_only_identity_cards_and_allows_decline(self):
        for accept in (False,True):
            with self.subTest(accept=accept):
                s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("61028")',
                    *self.hand("01088"),'puzzle.CreatePlayerDiscardPile("61004","61011","61025")',
                    self.use("61001a","Thwart","61028")],choose_other=self.choices(
                    names=("Shuffle all identity",) if accept else ()))
                for cid in ("61004","61011"):
                    self.assertEqual(cid in s[-1]["discard"],not accept)
                self.assertIn("61025",s[-1]["discard"])
                self.assertNotIn("61028",s[-1]["side_schemes"])

    def test_defend_our_city_requires_identity_defender_and_hinder_scales(self):
        for multiplayer,expected in ((False,4),(True,8)):
            with self.subTest(multiplayer=multiplayer):
                s=self.play([*self.hand("61029"),'puzzle.PutIntoPlay("61025")',
                    'puzzle.ChangeFormFor(0,"Hero")',self.use("61029","Play")],
                    configure_scene=self.two_players if multiplayer else None)
                self.assertNotIn(("61029","Play"),s[3]["actions"])
                self.assertEqual(self.face(s[-1],"61029")["threat"],expected)

    def test_defend_our_city_search_and_team_up_discount_expires(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("61003")',
            'puzzle.SetThreat("01097b",3)','puzzle.PutIntoPlay("61029")','puzzle.SetThreat("61029",3)',*self.hand("01088"),
            'puzzle.CreatePlayerDeck("61027")',self.use("61001a","Thwart","61029"),
            'puzzle.CreateEncounterDeck("01105","01104")','END_TURN'],
            choose_other=self.search("61027"))
        self.assertIn("61027",s[-3]["hand"])
        self.assertTrue(all(c=="0" for c in s[-3]["costs"]["61027"]))
        self.assertTrue(all(c=="1" for c in s[-1]["costs"]["61027"]))

    def test_starting_each_innate_can_enter_opening_hand_before_draw(self):
        for cid,name in (("61034","Innate Aggression"),("61036","Innate Perception"),("61037","Innate Inspiration")):
            with self.subTest(cid=cid):
                def configure(scene): scene.players[0].player_deck.append(cid)
                s=self.play([],configure_scene=configure,choose_other=self.choices(names=("Add "+name,)))[0]
                self.assertIn(cid,s["hand"])
                self.assertEqual(len(s["hand"]),6)
                self.assertEqual(sum(1 for p in self.last_prompts if any("(Starting)" in o["name"] for o in p.options)),1)

    def test_entrapment_stun_spends_costs_but_replaces_damage(self):
        s=self.play(['puzzle.PutIntoPlay("61024")','puzzle.Stun(hero)',
            'puzzle.CreateEncounterDeck("01104")','DoScheme("01094")'],
            choose_other=self.choices(responses=("61024",)))
        self.assertEqual(s[-1]["face"],"61001a")
        self.assertNotIn("61024",s[-1]["controlled"])
        self.assertFalse(s[-1]["stunned"])
        self.assertEqual(s[-2]["villain_health"],s[-1]["villain_health"])

    def test_entrapment_no_scheme_resolution_when_villain_is_confused(self):
        s=self.play(['puzzle.PutIntoPlay("61024")','puzzle.Confuse("01094")','DoScheme("01094")'],
            choose_other=self.choices(responses=("61024",))) [-1]
        self.assertEqual(s["face"],"61001b")
        self.assertIn("61024",s["controlled"])
        self.assertEqual(s["main_threat"],0)

    def test_righteous_purpose_other_controller_and_one_per_player(self):
        s=self.play(['puzzle.PutIntoPlay("01083")','puzzle.PutIntoPlayFor(1,"62012")',
            'puzzle.Damage("01083",2)','puzzle.Damage("62012",2)',
            *self.hand("62019","62025"),self.use("62019","Play","62001b"),
            *self.hand("62019","62025")],configure_scene=self.two_players)[-1]
        self.assertEqual(self.face(s,"62012")["atk"],4)
        self.assertEqual(self.face(s,"01083")["atk"],1)
        targets=[]
        for option in self.last_prompts[-1].options:
            if self.card_id(option)=="62019": targets=option["all_legal_targets"]
        self.assertEqual(targets,[self.face(s,"61001b")["id"]])
        self.assertIn("62019",[f.paper.card_id for f in self.last_game.world.const_players[1].supports.Get()])

    def test_defensive_formation_can_protect_other_players_defender(self):
        s=self.play(['puzzle.PutIntoPlay("62018")','puzzle.PutIntoPlayFor(1,"62012")',
            self.use("62018","Action","62012")],configure_scene=self.two_players)[-1]
        self.assertEqual(self.face(s,"62012")["tough"],1)

    def test_joys_of_life_can_exhaust_other_players_hero(self):
        s=self.play(['puzzle.ChangeFormFor(1,"Hero")','puzzle.Exhaust(hero)',
            *self.hand("61026"),self.use("61026")],configure_scene=self.two_players,
            choose_other=self.choices(names=("Exhaust a hero",))) [-1]
        self.assertFalse(self.face(s,"61001b")["exhausted"])
        self.assertTrue(self.face(s,"62001a")["exhausted"])
        self.assertFalse(self.face(s,"01097b")["exhausted"])

    def test_strategy_session_searches_chosen_players_deck(self):
        def configure(scene):
            self.two_players(scene)
            scene.players[1].player_deck.append("61028")
        s=self.play([*self.hand("61019","01088"),self.use("61019","Play","62001b")],
            configure_scene=configure,choose_other=self.search("61028"))
        self.assertEqual(s[-1]["players"][0]["hand"],[])
        self.assertEqual(len(s[-1]["players"][1]["hand"]),len(s[-2]["players"][1]["hand"])+1)
        self.assertIn("61028",s[-1]["players"][1]["hand"])

    def test_lay_the_trap_multiplayer_damage_scales(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("61021")',
            'puzzle.SetThreat("61021",3)',self.use("61001a","Thwart","61021")],configure_scene=self.two_players)
        self.assertEqual(s[-2]["villain_health"]-s[-1]["villain_health"],10)

    def test_lay_low_heals_existing_alter_ego_even_when_other_hero_declines_flip(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.Damage(hero,5)',
            'puzzle.Damage(world.const_players[1].GetIdentity(),5)','puzzle.PutIntoPlay("61039")',
            'puzzle.SetThreat("61039",3)',self.use("61001a","Thwart","61039")],
            configure_scene=self.two_players,choose_other=self.choices())[-1]
        self.assertEqual(s["players"][0]["face"],"61001a")
        self.assertEqual(s["players"][0]["hp"],6)
        self.assertEqual(s["players"][1]["hp"],9)

    def test_unbreakable_bond_works_with_other_players_identity(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.ChangeFormFor(1,"Hero")',
            'puzzle.Damage(world.const_players[1].GetIdentity(),4)','puzzle.SetThreat("01097b",6)',
            *self.hand("61027","01088"),self.use("61027")],configure_scene=self.two_players)[-1]
        self.assertEqual(s["players"][1]["hp"],9)
        self.assertEqual(s["main_threat"],3)

    def test_spider_woman_ignores_other_players_thwart_and_confused_attempt(self):
        s=self.play(['puzzle.PutIntoPlay("61016")','puzzle.ChangeFormFor(0,"Hero")',
            'puzzle.SetThreat("01097b",6)','puzzle.Confuse(hero)',self.use("61001a","Thwart","01097b"),
            'END_TURN','puzzle.ChangeFormFor(1,"Hero")',self.use("62001a","Thwart","01097b")],
            configure_scene=self.two_players,choose_other=self.choices(responses=("61016",))) [-1]
        self.assertEqual(self.face(s,"61016")["limb"],0)
        self.assertEqual(s["main_threat"],4)

    def test_shakedown_under_other_control_only_rewards_that_player(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.SetThreat("01097b",8)',
            *self.hand("61035","01088"),self.use("61035","Play","62001b"),
            'puzzle.PutIntoPlay("62029")','puzzle.Damage("62029",3)',self.use("61001a","Attack","62029"),
            'END_TURN','puzzle.ChangeFormFor(1,"Hero")','puzzle.PutIntoPlay("62029")',
            'puzzle.Damage("62029",3)',self.use("62001a","Attack","62029")],configure_scene=self.two_players,
            choose_other=self.choices(responses=("61035",),names=("Remove threat equal",)))
        self.assertEqual(s[7]["main_threat"],8)
        self.assertEqual(s[-1]["main_threat"],6)
        self.assertTrue(self.face(s[-1],"61035")["exhausted"])

    def test_shakedown_max_one_per_player(self):
        s=self.play([*self.hand("61035","01088"),self.use("61035","Play"),
            *self.hand("61035","01088")])[-1]
        self.assertNotIn(("61035","Play"),s["actions"])

    def test_black_belt_can_use_other_players_martial_artist_but_max_one_per_character(self):
        s=self.play(['puzzle.PutIntoPlayFor(1,"62012")',*self.hand("62037"),
            self.use("62037","Play","62001b"),*self.hand("62037")],configure_scene=self.two_players)[-1]
        self.assertIn("MARTIAL ARTIST",self.face(s,"62001b")["traits"])
        option=next(o for o in self.last_prompts[-1].options if self.card_id(o)=="62037")
        self.assertNotIn(self.face(s,"62001b")["id"],option["all_legal_targets"])
        self.assertIn(self.face(s,"61001b")["id"],option["all_legal_targets"])

    def test_innate_inspiration_does_not_buff_other_players_allies(self):
        s=self.play(['puzzle.PutIntoPlay("61037")','puzzle.PutIntoPlay("01083")',
            'puzzle.PutIntoPlayFor(1,"62012")'],configure_scene=self.two_players)[-1]
        self.assertEqual(self.face(s,"01083")["max_hp"],4)
        self.assertEqual(self.face(s,"62012")["max_hp"],3)

    def test_defend_our_city_search_and_discount_reach_each_player(self):
        def configure(scene):
            self.two_players(scene)
            scene.players[1].player_deck.append("61027")
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.ChangeFormFor(1,"Hero")',
            'puzzle.SetThreat("01097b",3)','puzzle.PutIntoPlay("61029")','puzzle.SetThreat("61029",3)',
            self.use("61001a","Thwart","61029"),'END_TURN'],configure_scene=configure,
            choose_other=self.search("61027"))
        for player in s[-2]["players"]: self.assertIn("61027",player["hand"])
        self.assertEqual(s[-2]["costs"]["61027"],["0"])
        self.assertEqual(s[-1]["costs"]["61027"],["0"])

    def test_valkyrie_can_save_other_players_ally(self):
        s=self.play(['puzzle.PutIntoPlay("62014")','puzzle.PutIntoPlayFor(1,"62012")',
            'puzzle.Damage("62012",5)'],configure_scene=self.two_players,
            choose_other=self.choices(responses=("62014",))) [-1]
        self.assertEqual(self.face(s,"62012")["hp"],1)
        self.assertFalse(any(f["cid"]=="62014" for f in s["field"]))

    def test_hulk_does_not_gain_rage_for_other_players_villain_attack(self):
        s=self.play(['puzzle.PutIntoPlay("62020")','puzzle.ChangeFormFor(1,"Hero")',
            'puzzle.CreateEncounterDeck("01104")',
            'puzzle.FindOrCreateFace("01094").DoAttackYou(world.const_players[1],DebugRule(hero))'],
            configure_scene=self.two_players,choose_other=self.choices(responses=("62020",))) [-1]
        self.assertEqual(self.face(s,"62020")["rage"],0)

    def test_toughen_up_uses_base_health_even_with_higher_maximum(self):
        self.pack="luke_cage"
        s=self.play(['puzzle.PutIntoPlay("62012")',*self.hand("62037"),self.use("62037","Play","62001b"),
            'puzzle.PutIntoPlay("62036")','puzzle.Damage(hero,5)',self.use("62001b","Recover")],
            choose_other=self.choices(responses=("62036",))) [-1]
        self.assertEqual(s["health"],10)
        self.assertEqual(self.face(s,"62001b")["max_hp"],11)
        self.assertEqual(s["tough"],1)

    def test_righteous_purpose_tracks_hero_health_and_form_changes(self):
        s=self.play(['puzzle.ChangeFormFor(0,"Hero")','puzzle.PutIntoPlay("62019")',
            'puzzle.Damage(hero,10)','puzzle.ChangeFormFor(0,"Identity")',
            'puzzle.ChangeFormFor(0,"Hero")','puzzle.Heal(hero,1)'])
        self.assertEqual(self.face(s[3],"61001a")["atk"],4)
        self.assertEqual(self.face(s[-2],"61001a")["thw"],5)
        self.assertEqual(self.face(s[-1],"61001a")["atk"],2)

    def test_mitigated_threat_paid_play_attaches_and_removes_icons(self):
        s=self.play(['puzzle.PutIntoPlay("01107")',*self.hand("61040"),self.use("61040","Play","01107")])[-1]
        self.assertEqual(s["hand"],[])
        scheme=next(f for f in self.last_game.world.area_schemes_side.Get() if f.paper.card_id=="01107")
        self.assertFalse(scheme.hazard)

    def test_starting_can_be_declined_without_adding_extra_opening_cards(self):
        def configure(scene): scene.players[0].player_deck.append("61034")
        s=self.play([],configure_scene=configure,choose_other=self.choices(names=("Leave Innate Aggression",)))[0]
        self.assertEqual(len(s["hand"]),6)
        self.assertNotIn("61034",s["hand"])


if __name__ == "__main__":
    unittest.main()
