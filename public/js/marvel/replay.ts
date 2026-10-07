import { ButtonSetting } from './settings.js'
import { Effect } from './effect.js'
import { Button } from './buttons.js'
import { SelectStep } from './select.js'
import { BtnOk } from './btn_ok.js'
import { Cards } from './cards.js'

export class Replay {
    static prepared_replay = false
    static preparing_replay = false
    static is_watching = false
    static finished = false
    private static endDialog: HTMLDivElement|undefined
    private static playbackGeneration = 0

    private static cancelPendingReplay() {
        Replay.playbackGeneration++
        Replay.prepared_replay = false
        Replay.preparing_replay = false
    }

    static setWatching(watching: boolean) {
        if( Replay.is_watching && !watching ) Replay.cancelPendingReplay()
        Replay.is_watching = watching
        if( !watching ) {
            Replay.finished = false
            Replay.endDialog?.remove()
            Replay.endDialog = undefined
        }
    }

    static onPrompt() {
        Replay.finished = Effect.response_json_ask.replay_finished
        if( !Replay.finished ) {
            Replay.endDialog?.remove()
            Replay.endDialog = undefined
            return
        }
        Replay.cancelPendingReplay()
        BtnOk.setDisable(true)
        if( Replay.endDialog ) return
        const dialog = document.createElement('div')
        dialog.id = 'replay-end-dialog'
        dialog.setAttribute('role', 'dialog')
        dialog.setAttribute('aria-modal', 'true')
        dialog.setAttribute('aria-labelledby', 'replay-end-title')
        dialog.style.cssText = 'position:fixed;inset:0;z-index:10000;background:#000b;display:flex;align-items:center;justify-content:center;font:16px Arial,sans-serif'
        const panel = document.createElement('div')
        panel.style.cssText = 'background:#242424;color:white;padding:24px;border-radius:16px;width:440px;max-width:calc(100vw - 32px);max-height:calc(100vh - 32px);overflow:auto;box-sizing:border-box;text-align:center'
        const title = document.createElement('h2')
        title.id = 'replay-end-title'
        title.textContent = 'End of recording'
        title.style.cssText = 'font-size:24px;line-height:32px;margin:0'
        const description = document.createElement('p')
        description.textContent = 'This saved game ends here. Choose Continue game to make new choices, or return to the replay library.'
        description.style.cssText = 'font-size:16px;line-height:24px;margin:16px 0'
        const continueButton = document.createElement('button')
        continueButton.textContent = 'Continue game'
        continueButton.style.cssText = 'font-size:16px;padding:8px 12px;margin:4px;cursor:pointer'
        continueButton.onclick = async () => {
            continueButton.disabled = true
            try {
                await Replay.continueGame()
            } catch( error ) {
                description.textContent = error instanceof Error ? error.message : 'Could not continue the game.'
                continueButton.disabled = false
            }
        }
        const libraryButton = document.createElement('button')
        libraryButton.textContent = 'Replay library'
        libraryButton.style.cssText = 'font-size:16px;padding:8px 12px;margin:4px;cursor:pointer'
        libraryButton.onclick = () => { window.location.href = '/replay' }
        panel.append(title, description, continueButton, libraryButton)
        dialog.append(panel)
        document.body.append(dialog)
        Replay.endDialog = dialog
        continueButton.focus()
    }

    static async continueGame() {
        const response = await fetch('continue_replay', { method: 'POST' })
        const result = await response.json()
        if( !response.ok ) throw new Error(result.error || 'Could not continue the game.')
        ButtonSetting.is_replay = 0
        Replay.prepared_replay = false
        Replay.preparing_replay = false
        Replay.setWatching(false)
        document.body.classList.remove('replaying')
        document.getElementById('replay-btn')?.classList.remove('clicked')
        const url = new URL(window.location.href)
        url.searchParams.delete('replay')
        window.history.replaceState(null, '', url)
        Button.doGet()
    }

    static doReplay(temp=false, delay=300, do_skip=false) {
        if( Replay.finished || Replay.prepared_replay || Replay.preparing_replay ) {
            return false
        }
        Replay.preparing_replay = true
        if( Effect.response_json_ask.replay_input != '{}' ) {
        const generation = Replay.playbackGeneration
        const cancelled = () => Replay.finished || generation != Replay.playbackGeneration
        const data = JSON.parse(Effect.response_json_ask.replay_input)
        setTimeout(async () => {
            if( cancelled() ) return
            let is_debug_command = false
            function sleep(ms: number) {
                return new Promise(resolve => setTimeout(resolve, ms));
            }

            if( data['id'].startsWith(":") ) {
                is_debug_command = true
            }
            else if( data['id'] != '' ) {
                const object_id = Number(data['id'].match(/c(\d+) /)[1])
                const card_div = Cards.getDiv(object_id)!

                if( SelectStep.isCard() ) {
                    await sleep(delay);
                    if( cancelled() ) return
                    Effect.onCardClick(card_div, false, true)
                }

                if( SelectStep.isEffect() ) {
                    await sleep(delay);
                    if( cancelled() ) return
                    const str = data['id'].match(/e(\d+) (.*) c(\d+)/)[2].replaceAll(" ", "_")
                    let buttons = Effect.options_button_div.querySelectorAll('button')
                    if( str == "Cancel" ) {
                        Effect.onCancel()
                    }
                    else
                    if( buttons.length == 1 ) {
                        buttons[0].click()
                    }
                    else {
                        for( let e of buttons ) {
                            const button_text = JSON.parse(e.dataset.json_str!)['name']
                            if( str == button_text) {
                                e.click()
                                break
                            }
                        }
                    }
                }

                if( !SelectStep.isTargets() && !SelectStep.isCost() ) {
                    // Some debug command like `Play('04016')` will create new card that not in the list so
                    // `Effect.clicking_card_div` will get null and `Effect.isExEffect()` failed in `onCardClick`
                    // `SelectStep.step` still in `card`
                    if( !SelectStep.isCard() ) {
                        Button.doPost(false)
                    }
                }
                if( SelectStep.isTargets() && data['targets'].length > 0 ) {
                    await sleep(delay);
                    if( cancelled() ) return
                    for( let res of data['targets'] ) {
                        const object_id = Number(res.match(/c(\d+) /)[1])
                        const card_div = Cards.getDiv(object_id)!
                        Effect.onCardClick(card_div, false, true)
                    }
                }

                if( !SelectStep.isCost() ) {
                    if( BtnOk.btn_end_div.classList.contains('ok') ||
                        !BtnOk.btn_ok_div.disabled ) {
                        Button.doPost(false)
                    } else {
                        // if( data['id'].includes('Cancel') ) {
                        //     Button.doCancel()
                        // }
                    }
                }
                if( SelectStep.isCost() &&  data['resources'].length > 0 ) {
                    await sleep(delay);
                    if( cancelled() ) return
                    for( let res of data['resources'] ) {
                        const object_id = Number(res.match(/c(\d+) /)[1])
                        const card_div = Cards.getDiv(object_id)!
                        Effect.onCardClick(card_div, false, true)
                    }
                }
            }
            Replay.prepared_replay = true
            Replay.preparing_replay = false

            if( ButtonSetting.is_replay || temp ) {
                setTimeout(() => {
                    if( cancelled() || !(ButtonSetting.is_replay || temp) ) return
                    document.querySelectorAll('.deck.clicked').forEach( deck_div => {
                        deck_div.classList.remove('clicked')
                    })
                    if( is_debug_command ) {
                        Button.doNext()
                    }
                    else if( SelectStep.isCost() ) {
                        Button.doPost(true)
                    } else {
                        Button.doCancel()
                    }
                    if( do_skip ) {
                        Button.doToEnd()
                    }
                }, delay);
            }
        }, 100);
        }
    }

}
