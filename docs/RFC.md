# RFC process

Proposals that change public APIs, block schemas, or checkpoint formats require a short RFC before merge.

## Template

1. **Summary** — one paragraph
2. **Motivation** — problem and Document 2 section reference
3. **Design** — API/schema changes, migration plan
4. **Alternatives** — what was rejected
5. **Rollout** — phases, feature flags, EE impact

## Process

1. Open a GitHub issue labeled `rfc` with the template filled in.
2. Discuss for at least 48 hours (or async review on the PR).
3. Merge implementation only after RFC issue is linked in the PR description.

Breaking changes to the 17-type `BlockType` union or Plan JSON schema require a **major** version bump in release notes.
