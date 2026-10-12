export interface ArtworkStatus {
    state: string;
    ready: boolean;
    can_play: boolean;
    completed_cards: number;
    total_cards: number;
    completed_packs: number;
    total_packs: number;
    downloaded_bytes: number;
    total_bytes: number;
    installed_bytes: number;
    required_bytes: number;
    required_storage_bytes: number;
    total_installed_bytes: number;
    folder: string;
    error?: string;
    errors?: Record<string, string>;
}

export function formatArtworkBytes(bytes: number): string {
    if (!Number.isFinite(bytes) || bytes < 0) return 'Not available';
    const unit = bytes >= 1024 ** 3 ? 'GiB' : bytes >= 1024 ** 2 ? 'MiB' : 'KiB';
    const divisor = unit === 'GiB' ? 1024 ** 3 : unit === 'MiB' ? 1024 ** 2 : 1024;
    return `${(bytes / divisor).toFixed(1)} ${unit} (${bytes.toLocaleString()} bytes)`;
}

export function artworkDestination(raw: string | null, origin: string): string {
    if (!raw) return '/main';
    let destination: URL;
    try { destination = new URL(raw, origin); }
    catch { return '/main'; }
    const page = destination.pathname.replace(/^\/public\//, '/').replace(/\.html$/, '');
    const allowed = ['/', '/main', '/deck', '/cards', '/scene', '/replay', '/puzzle', '/puzzle_editor', '/puzzle_test', '/marvel', '/watch'];
    return destination.origin === origin && allowed.includes(page)
        ? destination.pathname + destination.search : '/main';
}

// Keep the originating page and uploaded save in memory while preparation runs.
export function showArtworkPreparation(retry: () => void): void {
    document.getElementById('artwork-selection-notice')?.remove();
    const notice = document.createElement('aside');
    notice.id = 'artwork-selection-notice';
    notice.setAttribute('role', 'status');
    notice.style.cssText = 'position:fixed;right:20px;bottom:20px;max-width:420px;padding:20px;background:#253244;color:white;border:1px solid #80d5ff;border-radius:8px;z-index:99999;font:16px Arial;box-shadow:0 8px 30px #0008';
    const message = document.createElement('p');
    message.textContent = 'Artwork for this selection is still being prepared. Your selection is kept. Check preparation, then retry when it finishes.';
    notice.appendChild(message);
    const link = document.createElement('a');
    link.href = '/artwork'; link.target = '_blank'; link.rel = 'noopener';
    link.textContent = 'View artwork'; link.style.color = '#80d5ff';
    notice.appendChild(link);
    for (const [label, action] of [
        ['Retry selection', () => { notice.remove(); retry(); }],
        ['Dismiss', () => notice.remove()],
    ] as const) {
        const control = document.createElement('button');
        control.type = 'button'; control.textContent = label;
        control.style.marginLeft = '12px'; control.onclick = action;
        notice.appendChild(control);
    }
    document.body.appendChild(notice);
}

export function startArtworkPage(): void {
    const text = (id: string, value: string) => { document.getElementById(id)!.textContent = value; };
    const button = (id: string) => document.getElementById(id) as HTMLButtonElement;
    const progress = document.getElementById('progress') as HTMLProgressElement;
    const next = new URLSearchParams(location.search).get('next');
    const destination = artworkDestination(next, location.origin);
    let status: ArtworkStatus | null = null;
    let actionRunning = false;
    let timer: number | undefined;

    function render(value: ArtworkStatus): void {
        status = value;
        const preparing = ['idle', 'preparing', 'downloading'].includes(value.state);
        const titles: Record<string, string> = {
            idle: 'Preparing your collection', preparing: 'Preparing your collection', downloading: 'Downloading artwork',
            paused: 'Download paused', ready: 'Your artwork is ready', error: 'Preparation needs attention', incomplete: 'Artwork catalog is incomplete',
        };
        text('state', titles[value.state] || 'Preparing artwork');
        text('message', value.ready ? 'Artwork for all cards supported by this build is saved locally and ready to use.'
            : value.can_play ? 'Installed content is ready. New content becomes available as its artwork finishes.'
            : value.state === 'incomplete' ? 'This build does not yet contain a complete verified artwork catalog. A corrected build is needed before first-time preparation can finish.'
            : value.state === 'paused' ? 'Resume whenever you are ready. Completed downloads are kept.'
            : 'Preparing the complete collection before play. Progress is saved automatically.');
        progress.max = Math.max(1, value.total_cards);
        progress.value = value.completed_cards;
        text('cards', `${value.completed_cards.toLocaleString()} / ${value.total_cards.toLocaleString()}`);
        text('packs', `${value.completed_packs.toLocaleString()} / ${value.total_packs.toLocaleString()}`);
        text('download', `${formatArtworkBytes(value.downloaded_bytes)} / ${formatArtworkBytes(value.total_bytes)}`);
        text('installed', `${formatArtworkBytes(value.installed_bytes)} / ${formatArtworkBytes(value.total_installed_bytes)}`);
        text('required', formatArtworkBytes(value.required_storage_bytes));
        text('folder', value.folder || 'Not available');
        const errors = [value.error, ...Object.values(value.errors || {})].filter(Boolean);
        text('errors', [...new Set(errors)].join('\n'));
        document.getElementById('errors')!.hidden = errors.length === 0;
        button('pause').disabled = actionRunning || !preparing;
        button('resume').disabled = actionRunning || value.state !== 'paused';
        button('retry').disabled = actionRunning || value.state !== 'error';
        button('continue').disabled = !value.can_play;
        button('continue').textContent = value.ready ? 'Continue' : 'Continue with installed content';
        if (next && value.can_play) location.replace(destination);
    }

    async function poll(): Promise<void> {
        try {
            const response = await fetch('/get_artwork_status', { cache: 'no-store' });
            if (!response.ok) throw new Error('Could not read artwork status');
            if (response.headers.get('Content-Type')?.includes('text/html')) {
                // Authentication/version pages are returned as HTML by the
                // existing server. Let their normal cookie flow recover.
                location.reload();
                return;
            }
            render(await response.json());
        } catch {
            text('state', 'Waiting for the game host');
            text('message', 'Keep the game host open. This page will reconnect automatically.');
        } finally {
            timer = window.setTimeout(poll, 1000);
        }
    }

    async function action(name: string): Promise<void> {
        actionRunning = true;
        if (status) render(status);
        try {
            const response = await fetch('/artwork_action', {
                method: 'POST', cache: 'no-store', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: name }),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Could not update artwork download');
            render(result);
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            if (status) status = { ...status, error: message };
            else { text('errors', message); document.getElementById('errors')!.hidden = false; }
        } finally {
            actionRunning = false;
            if (status) render(status);
        }
    }

    for (const name of ['pause', 'resume', 'retry']) button(name).onclick = () => { void action(name); };
    button('continue').onclick = () => { if (status?.can_play) location.assign(destination); };
    window.addEventListener('pagehide', () => { if (timer !== undefined) window.clearTimeout(timer); }, { once: true });
    void poll();
}
