/**
 * GitHub Integration Type Definitions
 * Supporting SCRUM-11: PR & Commit Lifecycle Tracking
 */

export interface GithubAuthConfig {
    clientId: string;
    clientSecret: string;
    appId: string;
    installationId?: string;
}

export interface GithubPRMetadata {
    id: number;
    number: number;
    title: string;
    author: string;
    additions: number;
    deletions: number;
    reviewCycles: number;
    createdAt: string;
    mergedAt?: string;
    timeToMergeHours?: number;
}

export interface GithubWebhookPayload {
    action?: 'opened' | 'synchronize' | 'closed' | 'merged';
    pull_request?: {
        id: number;
        number: number;
        title: string;
        user: { login: string };
        additions: number;
        deletions: number;
        created_at: string;
        merged_at?: string;
    };
    commits?: Array<{
        id: string;
        message: string;
        author: { name: string };
        timestamp: string;
    }>;
    repository: {
        full_name: string;
        id: number;
    };
}

export interface RepoConfig {
    repoId: number;
    isEnabled: boolean;
    trackingBranches: string[];
}
