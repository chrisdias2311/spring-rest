/**
 * JIRA Integration Type Definitions
 * Supporting SCRUM-104: Bi-Directional Issue Sync
 */

export interface JiraAuthConfig {
    clientId: string;
    clientSecret: string;
    redirectUri: string;
    scopes: string[];
}

export interface JiraIssue {
    id: string;
    key: string;
    fields: {
        summary: string;
        status: {
            name: string;
            id: string;
        };
        assignee?: {
            displayName: string;
            accountId: string;
        };
        updated: string;
    };
}

export interface JiraWebhookPayload {
    timestamp: number;
    webhookEvent: 'jira:issue_created' | 'jira:issue_updated' | 'jira:issue_deleted';
    issue: JiraIssue;
    user?: {
        displayName: string;
    };
}

export interface SyncResult {
    status: 'SUCCESS' | 'FAILURE' | 'RETRY_QUEUED';
    externalId: string;
    internalId?: string;
    error?: string;
}
