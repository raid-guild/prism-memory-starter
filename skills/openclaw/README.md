# OpenClaw Skill Uploads

This starter ships with one ready-to-upload OpenClaw skill:

- `skills/openclaw/prism-memory-ops`

Use it for a general operations agent that can run memory pipeline checks, targeted reruns, and knowledge validation/index maintenance from this repo.

## Upload modal fields

- **Skill folder**: choose all files from the skill folder (including nested `references/` files)
- **Name**: match SKILL frontmatter `name`
- **Description**: use SKILL frontmatter `description` (or leave optional field blank if UI reads from `SKILL.md`)

## Required file

Each skill folder includes:

- `SKILL.md` with YAML frontmatter (`name`, `description`)

Optional supporting files:

- `agents/openai.yaml`
- `references/*.md`
