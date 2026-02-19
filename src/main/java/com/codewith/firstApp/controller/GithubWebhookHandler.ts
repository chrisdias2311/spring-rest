import { GithubIntegrationService } from './GithubIntegrationService';
import { GithubWebhookPayload } from './GithubTypes';

/**
 * GithubWebhookHandler
 * 
 * Listens for repository events from GitHub and translates them 
 * into delivery intelligence signals.
 */
export class GithubWebhookHandler {
    constructor(private githubService: GithubIntegrationService) { }

    /**
     * Endpoint: POST /webhooks/github
     */
    public async handleEvent(headers: any, body: any): Promise<{ status: string }> {
        const eventType = headers['x-github-event'];
        const signature = headers['x-hub-signature-256'];

        console.log(`[GITHUB_WEBHOOK] Received '${eventType}' event.`);

        // 1. Signature Validation (Critical for Security)
        if (!this.verifySignature(signature, body)) {
            console.error('[GITHUB_WEBHOOK] Signature mismatch. Rejecting event.');
            return { status: 'UNAUTHORIZED' };
        }

        const payload = body as GithubWebhookPayload;

        // 2. Event Routing Logic
        switch (eventType) {
            case 'pull_request':
                await this.githubService.trackPullRequest(payload);
                break;
            case 'push':
                await this.githubService.monitorCommits(payload);
                break;
            default:
                console.log(`[GITHUB_WEBHOOK] Event type '${eventType}' not currently tracked.`);
        }

        return { status: 'ACCEPTED' };
    }

    private verifySignature(sig: string, payload: any): boolean {
        // Mock SHA-256 HMAC verification against App Secret
        return !!sig;
    }
}
