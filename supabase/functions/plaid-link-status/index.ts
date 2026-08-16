import { handleHostedLinkStatus } from '../_shared/plaid-hosted-link.ts';
import { createHostedLinkDependencies } from '../_shared/plaid-runtime.ts';

Deno.serve((request) =>
  handleHostedLinkStatus(request, createHostedLinkDependencies())
);
