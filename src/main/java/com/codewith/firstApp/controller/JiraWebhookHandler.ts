import { JiraIntegrationService } from './JiraIntegrationService';
import { JiraWebhookPayload } from './JiraTypes';

/**
 * JiraWebhookHandler
 * 
 * Entry point for Atlassian JIRA Webhook Events.
 * Handles request validation and dispatches to the sync service.
 */
export class JiraWebhookHandler {
    constructor(private syncService: JiraIntegrationService) { }

    /**
     * POST /webhooks/jira
     */
    public async handleWebhook(body: any, signature: string): Promise<{ statusCode: number }> {
        console.log('[JIRA_WEBHOOK] Received incoming signal from Atlassian...');

        // 1. Security check: Validate Webhook Signature
        if (!this.isValidSignature(signature)) {
            console.warn('[JIRA_WEBHOOK] SECURITY ALERT: Invalid signature detected.');
            return { statusCode: 401 };
        }

        const payload = body as JiraWebhookPayload;

        // 2. Dispatch to Sync Engine
        const result = await this.syncService.syncIssue(payload);

        if (result.status === 'SUCCESS') {
            return { statusCode: 200 };
        }

        return { statusCode: 202 }; // Accepted for retry/processing
    }

    private isValidSignature(sig: string): boolean {
        // Mock HMAC verification logic
        return !!sig;
    }
}
