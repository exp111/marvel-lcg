interface SetInfoObject {
    name?: string;
    scenarios?: string[];
    underlings?: string[];
    fixed_scenarios?: string[];
    heroes?: string[];
    encounters?: string[];
    max_id?: string;
}

export class SetInfo {
    name: string;
    scenarios: string[];
    underlings: string[];
    fixed_scenarios: string[];
    heroes: string[];
    encounters: string[];
    max_id: string;

    constructor(obj: SetInfoObject | null = null) {
        this.name = '';
        this.scenarios = [];
        this.underlings = [];
        this.fixed_scenarios = [];
        this.heroes = [];
        this.encounters = [];
        this.max_id = '';

        if (obj) {
            this.name = obj.name || '';
            this.scenarios = obj.scenarios || [];
            this.underlings = obj.underlings || [];
            this.fixed_scenarios = obj.fixed_scenarios || [];
            this.heroes = obj.heroes || [];
            this.encounters = obj.encounters || [];
            this.max_id = obj.max_id || '';
        }
    }
}

