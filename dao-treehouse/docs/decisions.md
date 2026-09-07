# Technical Decisions

## GitHub Access

Use a GitHub App installed only on repositories selected by the user. The first release requests read-only Contents and Metadata permissions. This supports private repositories without asking for account-wide administration access.

The scanner pins every run to a commit SHA. GitHub login and repository access are separate from wallet identity.

## Wallet Connection

Start with Reown AppKit, wagmi, and viem. This suits DAO contributors who already use an external wallet and keeps signing in the wallet they control.

Use Safe Protocol Kit to inspect and construct Safe transactions. Use Safe API Kit only when the user chooses to propose a reviewed transaction to the Safe Transaction Service.

Privy is deferred. It is useful for application login and embedded-wallet onboarding, but embedded custody adds unnecessary scope to a governance operations MVP. It can be added later for team identity without replacing external-wallet and Safe flows.

## Application Structure

- Next.js and TypeScript web application
- separate TypeScript scan worker
- viem-based chain adapters
- `@xyflow/react` control graph
- shared Zod models with JSON Schema exports
- SQLite for the local prototype and PostgreSQL for hosted use

Package versions will be selected and locked when implementation begins. No dependency scaffold is added during the design stage.

## Source Verification

Use Sourcify v2 as the first open verification source, then supported explorer APIs where needed. Preserve source attribution and bytecode-match status. A verified source improves confidence but does not replace live storage and role checks.

## Action Handoff

The order of capability is fixed:

1. read-only discovery
2. unsigned JSON and Safe Transaction Builder export
3. fork simulation
4. optional Safe proposal submission
5. status tracking

Direct execution from the application is not part of the initial product.

## Official References

- [GitHub App permissions](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app)
- [Safe SDK overview](https://docs.safe.global/sdk/overview)
- [Safe API Kit](https://docs.safe.global/sdk/api-kit)
- [Reown AppKit React installation](https://docs.reown.com/appkit/react/core/installation)
- [Privy documentation](https://docs.privy.io/)
- [OpenZeppelin access control](https://docs.openzeppelin.com/contracts/5.x/access-control)
- [OpenZeppelin proxy contracts](https://docs.openzeppelin.com/contracts/5.x/api/proxy)
- [Sourcify v2 API](https://docs.sourcify.dev/docs/api/)
