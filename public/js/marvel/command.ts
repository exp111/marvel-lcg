import { Cards } from "./cards.js";
import { Notify } from "./notify.js";

export class Command {

    private static newWindow: Window|null = null
    private static savingReplay = false

    static setLastClickCard(card_div: HTMLElement) {
        if( Command.newWindow && !Command.newWindow.closed ) {
            const card = Cards.getCard(Number(card_div.dataset.id!))!
            const data = {
                type: 'setLastClickCard',
                card_object_id: card_div.dataset.id,
                card_id: card.card_id,
                card_name: card.name,
            };
            Command.newWindow.postMessage(data, '*')
            Command.newWindow.focus();
            return true
        }
        else {
            return false
        }
    }

    static async saveLocal() {
        if( Command.savingReplay ) return
        Command.savingReplay = true
        try {
            const response = await fetch("save_local", { method: 'POST' })
            if( !response.headers.get('Content-Type')?.includes('application/json') ) {
                throw new Error('The server returned an unexpected save response. Reload the game page.')
            }
            const result = await response.json()
            if( !response.ok || !result.path ) {
                throw new Error(result.error || 'The replay could not be saved.')
            }
            Notify.create('REPLAY', '', `Saved to ${result.path}. Open Replay on the main menu to watch.`, 6)
        } catch( error ) {
            Notify.create('SAVE FAILED', '', error instanceof Error ? error.message : 'The replay could not be saved.', 6)
        } finally {
            Command.savingReplay = false
        }
    }

    static async uploadSave(save_type: "Bug"|"Crash"|"Share", comment: string="") {
        if( Command.newWindow && !Command.newWindow.closed ) {
            Command.newWindow.close()
        }
        // window.open(`report.html?save_type=${save_type}`, "newWindow", "width=400,height=320");
        // Open the new window
        Command.newWindow = window.open(`report`, "newWindow", "width=400,height=320")!;

        const data = {
            type: 'uploadSave',
            save_type: save_type,
            comment: comment
        };

        // Send data to the new window once it has loaded
        Command.newWindow.onload = () => {
            Command.newWindow!.postMessage(data, '*'); // Use '*' to allow any origin or specify the target origin
        };
    }
}
