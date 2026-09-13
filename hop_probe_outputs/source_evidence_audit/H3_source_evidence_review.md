# H3 source-evidence audit

Assistant review proposals; no human review fields were filled and no source files were changed.

## Findings

- Inspected all 60 completions for 20 existing test questions.
- 15 chains have source-supported proposed labels, 4 need adjudication, and 41 should be excluded under the current output-quality policy.
- Only five question groups have at least two non-rejected completions. Even the optimistic count is below the notebook’s ten matched test-question requirement.
- No retained natural-error chain is fully adjudicated. This is a diagnostic assessment, not an H3 performance result.

## Concrete examples

- Crime Against Joe, sample 1: proposed labels [0, 0, 0]; film title, release date, and Henry Calvin role are supported.
- Issa Cissokho/Mali, sample 0, hop 4: a clear discrepancy. The generated hop places the Niger and Senegal rivers on the northern border; the context places them in the southern part. Other hops in that same chain remain unresolved.
- Craig Goldy, sample 1, hop 2: being called a vocalist is not established here, but guitarist and vocalist are not mutually exclusive. Leave unresolved.

## Recommended next steps

1. Preserve this run, its cached features, and the completed H1 result.
2. Do not spend time filling every blank simply to meet the review counter; the current test pool cannot meet the ten-question pairing requirement under this review policy.
3. Improve the generation protocol using training questions only: separate demonstrations from the target, reject copied examples and procedural outputs, and pilot before scaling.
4. Because this test set has now been inspected to diagnose the generator, reserve fresh held-out questions for final confirmatory H3 evaluation after changing the generation protocol.
5. Review factual errors versus missing evidence explicitly. Keep assistant proposals distinguishable from human-confirmed annotations.

## Per-chain proposals

| Generation ID | Proposal | Hop labels (null = unresolved) |
|---|---|---|
| 5a714a535542994082a3e77e-organic-0 | reject | Not labeled |
| 5a714a535542994082a3e77e-organic-1 | supported | [0, 0, 0] |
| 5a714a535542994082a3e77e-organic-2 | reject | Not labeled |
| 5a7330455542991f9a20c677-organic-0 | supported | [0, 0, 0] |
| 5a7330455542991f9a20c677-organic-1 | supported | [0, 0, 0] |
| 5a7330455542991f9a20c677-organic-2 | supported | [0, 0] |
| 5a77304d55429972597f1485-organic-0 | reject | Not labeled |
| 5a77304d55429972597f1485-organic-1 | reject | Not labeled |
| 5a77304d55429972597f1485-organic-2 | reject | Not labeled |
| 5a79c8c4554299148911fa4f-organic-0 | unresolved | [0, null, 0, 1, null] |
| 5a79c8c4554299148911fa4f-organic-1 | reject | Not labeled |
| 5a79c8c4554299148911fa4f-organic-2 | reject | Not labeled |
| 5a7a1ceb5542996c55b2dd13-organic-0 | reject | Not labeled |
| 5a7a1ceb5542996c55b2dd13-organic-1 | supported | [0, 0] |
| 5a7a1ceb5542996c55b2dd13-organic-2 | reject | Not labeled |
| 5a7ea45c5542994959419a3e-organic-0 | reject | Not labeled |
| 5a7ea45c5542994959419a3e-organic-1 | reject | Not labeled |
| 5a7ea45c5542994959419a3e-organic-2 | reject | Not labeled |
| 5a843610554299123d8c21e1-organic-0 | reject | Not labeled |
| 5a843610554299123d8c21e1-organic-1 | reject | Not labeled |
| 5a843610554299123d8c21e1-organic-2 | reject | Not labeled |
| 5a84a7305542997175ce1f14-organic-0 | reject | Not labeled |
| 5a84a7305542997175ce1f14-organic-1 | supported | [0, 0, 0, 0, 0, 0, 0] |
| 5a84a7305542997175ce1f14-organic-2 | unresolved | [0, 0, null, null, null] |
| 5a8581c25542991dd0999e61-organic-0 | reject | Not labeled |
| 5a8581c25542991dd0999e61-organic-1 | reject | Not labeled |
| 5a8581c25542991dd0999e61-organic-2 | reject | Not labeled |
| 5a8b53225542997f31a41cda-organic-0 | reject | Not labeled |
| 5a8b53225542997f31a41cda-organic-1 | reject | Not labeled |
| 5a8b53225542997f31a41cda-organic-2 | reject | Not labeled |
| 5a8d7ebd55429941ae14dfdb-organic-0 | supported | [0] |
| 5a8d7ebd55429941ae14dfdb-organic-1 | supported | [0, 0, 0] |
| 5a8d7ebd55429941ae14dfdb-organic-2 | supported | [0, 0, 0, 0] |
| 5ab25db35542993be8fa98e5-organic-0 | reject | Not labeled |
| 5ab25db35542993be8fa98e5-organic-1 | unresolved | [0, null, 0, 0] |
| 5ab25db35542993be8fa98e5-organic-2 | reject | Not labeled |
| 5abddc0a5542991f66106077-organic-0 | reject | Not labeled |
| 5abddc0a5542991f66106077-organic-1 | reject | Not labeled |
| 5abddc0a5542991f66106077-organic-2 | reject | Not labeled |
| 5ac326af554299657fa290ea-organic-0 | supported | [0, 0, 0, 0, 0, 0, 0] |
| 5ac326af554299657fa290ea-organic-1 | supported | [0, 0, 0, 0, 0] |
| 5ac326af554299657fa290ea-organic-2 | supported | [0, 0, 0] |
| 5add381f5542990dbb2f7dcf-organic-0 | reject | Not labeled |
| 5add381f5542990dbb2f7dcf-organic-1 | supported | [0, 0, 0, 0] |
| 5add381f5542990dbb2f7dcf-organic-2 | reject | Not labeled |
| 5adea3d95542997c77adee95-organic-0 | reject | Not labeled |
| 5adea3d95542997c77adee95-organic-1 | reject | Not labeled |
| 5adea3d95542997c77adee95-organic-2 | reject | Not labeled |
| 5adf3b905542992d7e9f92fb-organic-0 | unresolved | [0, 0, null, 0, 0, 0] |
| 5adf3b905542992d7e9f92fb-organic-1 | reject | Not labeled |
| 5adf3b905542992d7e9f92fb-organic-2 | reject | Not labeled |
| 5ae2c5105542996483e64a4e-organic-0 | reject | Not labeled |
| 5ae2c5105542996483e64a4e-organic-1 | supported | [0, 0, 0, 0, 0] |
| 5ae2c5105542996483e64a4e-organic-2 | supported | [0, 0, 0] |
| 5ae4c2835542995dadf243ec-organic-0 | reject | Not labeled |
| 5ae4c2835542995dadf243ec-organic-1 | reject | Not labeled |
| 5ae4c2835542995dadf243ec-organic-2 | reject | Not labeled |
| 5ae657395542992ae0d162e0-organic-0 | reject | Not labeled |
| 5ae657395542992ae0d162e0-organic-1 | reject | Not labeled |
| 5ae657395542992ae0d162e0-organic-2 | reject | Not labeled |

The companion JSON contains the question, exact generated hops, supporting context, supporting-sentence metadata, and explanation for every proposal.
