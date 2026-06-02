# Commercial Studio UX Research

Status: draft  
Date: 2026-06-03  
Scope: TASK-013 candidate, nontechnical creator experience for the automatic talking-head video product.

## Competitive Patterns

Reviewed public product/documentation surfaces for HeyGen, Synthesia, D-ID, and Captions.

- HeyGen positions avatar video creation around choosing or cloning an avatar, pairing it with a voice, entering text/script, then generating and sharing the video. Their public API docs also make avatar and voice the core inputs.
- Synthesia emphasizes a non-camera workflow: start from prompt/script/document, customize avatar/brand, optionally add visuals, then generate/export. Their public page also highlights Brand Kit, templates, captions, analytics, collaboration, and enterprise security as product navigation concepts.
- D-ID frames the product as a Creative Reality Studio for AI video generation, with avatar-led video as the primary object.
- Captions positions the product around AI editing for creators: script, avatar, captions, music, and social-ready output.

## Product Direction

The product should not present `Job`, `Pipeline`, `QC`, or raw environment variables as first-class concepts to operators. Those remain available in diagnostics for support and admin users, but the commercial default should be:

1. Write the idea.
2. Choose voice and avatar.
3. Pick caption/music/brand style.
4. Generate, preview, fix, download.

## UX Decisions Applied

- Replace engineering vocabulary with creator vocabulary.
- Keep the 9:16 preview central and large because the video is the product.
- Show readiness checks in human language: content, voice authorization, avatar authorization, voice service.
- Translate missing `COSYVOICE_BASE_URL` into "还没连接语音服务" on the main surface.
- Keep technical pipeline details under a collapsible "技术诊断" section.
- Keep asset management in the same screen so a nontechnical user does not need to understand API preconditions.

## Figma Artifact

Created a Figma direction file:

https://www.figma.com/design/HGigMRhTazlUpo3jvfSixu

The Figma draft maps the commercial studio layout: creator input, 4-step workflow, phone preview, readiness checks, asset shelf, and recent generated videos.
