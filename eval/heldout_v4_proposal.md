# Held-out v4: selection (approved by the author on 2026-11-26)

Candidates: `eval/heldout_v4_candidates.csv`, 100 real forum posts collected without looking at the docs and checked by reading the RST files. An LLM drafted the wording, facts and spans, as for v3. Nothing here has been run through the system.

## Proposed rule (same as v3)

- All `suggest=yes` answerable and partly rows that share no primary passage with the 175 dev questions (ADR 3): **28**.
- 18 `suggest=yes` unanswerable rows, round-robin across sites in cid order: **18**.
- Total **46** (28 answerable, 18 unanswerable). There are no comparison questions.

## Dropped by the shared-passage rule

| Candidate | Shares a primary passage with dev |
| --- | --- |
| c007 | v3-c110 |
| c014 | v3-c006, v3-c060 |
| c018 | v2-50 |
| c019 | face-varying, v2-37 |
| c033 | v2-22 |
| c041 | constant-vs-uniform |
| c054 | v3-c076 |
| c063 | v3-c049 |
| c064 | v2-03 |
| c077 | v3-c047 |
| c080 | v3-c091 |
| c097 | v3-c053 |
| c098 | v2-17 |

## Answerable

| cid | verdict | kind | site | question |
| --- | --- | --- | --- | --- |
| c006 | partly | paraphrase | aousd-forum | Can several threads edit the layers of one stage at the same time, and can other threads read from the stage while one thread is editing it? |
| c013 | partly | lookup | aousd-forum | Can I create a USD stage that lives only in memory, without any filesystem access? |
| c016 | answerable | lookup | aousd-forum | In an SdfPathExpression for a collection, how do I match prims at any depth of the hierarchy, and how do I add an extra condition, such as requiring that the prim has MaterialBindingAPI applied? |
| c022 | partly | paraphrase | aousd-forum | A prim inherits from a class that sets an attribute, and a variant selected on the same prim also sets that attribute. The variant selection is reported correctly, but the variant's value doesn't come through. Which opinion should win, and why? |
| c023 | answerable | paraphrase | aousd-forum | Instance prims can be overridden, but properties on prims beneath them cannot. Does that also apply to primvars? Do constant primvars authored on an instance prim still reach the geometry inside the instance? |
| c025 | partly | paraphrase | aousd-forum | My crowd asset's variant selections are driven by expression variables. In the shot layer I reference the asset several times. Where are expression variables authored, and can the shot override the values the referenced asset uses? |
| c029 | partly | lookup | aousd-forum | Is there an officially registered MIME type for USD content, for example for .usdz packages? |
| c032 | answerable | paraphrase | aousd-forum | Our understanding was that a portal light is just a rectangle with a transform, associated with a dome light. Why does UsdLuxPortalLight carry the full set of light attributes, such as intensity and exposure? Was that intentional, and what are they for? |
| c037 | answerable | paraphrase | aousd-forum | When I remove content from a binary .usdc layer and save it, the file on disk doesn't get smaller. Is that by design, and how can I get a compact file again? |
| c043 | partly | paraphrase | github-issues | Maya works in centimeters while Houdini and Katana work in meters. Does USD record the linear unit a scene was authored in, so that content authored at different scales can be combined correctly? |
| c045 | answerable | lookup | github-issues | Given a prim whose type is Mesh, how can I check whether its schema class derives from UsdGeomXformable? |
| c047 | answerable | paraphrase | github-issues | I exported an animation from Blender with constant (stepped) keys, but in USD the values are linearly interpolated between time samples. How can I get stepped, held interpolation of time samples in USD? |
| c052 | answerable | paraphrase | github-issues | How should kind metadata be arranged down a prim hierarchy? Can a component contain other component models, and can a prim with no kind sit between a group and the component below it? |
| c055 | partly | paraphrase | github-issues | For UsdUVTexture's sourceColorSpace, does the value sRGB describe only the transfer curve, or the gamut of the image as well? |
| c056 | answerable | paraphrase | github-issues | Can a variant modify metadata on the prim that owns the variant set, for example adding a references list inside a variant so that each variant brings in a different asset? |
| c057 | answerable | lookup | github-issues | When I create a layer with the plain .usd extension and don't pass a format argument, how is its encoding chosen, and which environment variable controls it? |
| c059 | answerable | paraphrase | github-issues | An asset I downloaded declares doubleSided as a varying attribute, although the schema declares it uniform. Should such a file be rejected, or should the attribute be read as uniform? Does USD itself enforce variability? |
| c061 | answerable | lookup | github-issues | Should a UsdPrimvarReader's inputs:varname be authored as a token or as a string? I see a mix of both in files I receive. |
| c062 | answerable | lookup | github-issues | Can a usdz package contain other usdz packages? The list of allowed file types in the usdz specification doesn't mention usdz. |
| c068 | partly | paraphrase | sidefx-forum | Our assets are instanceable assemblies containing payloaded components. I open the stage with nothing loaded and then traverse for prims of kind component to load them, but the traversal never visits anything under the instances. Why does traversal stop there? |
| c069 | answerable | paraphrase | sidefx-forum | A camera referenced from a matchmove Alembic comes in with every attribute animated. Without editing the source file, how can I make one attribute, such as horizontalAperture, static while keeping its default value? |
| c070 | partly | paraphrase | sidefx-forum | What is a value clip set, and can a prim have more than one clip set under different names? |
| c071 | answerable | paraphrase | sidefx-forum | After upgrading, meshes that have a material:binding relationship no longer get their materials. The prims don't have MaterialBindingAPI in their apiSchemas. Is applying that schema required for a binding to count? |
| c072 | partly | paraphrase | sidefx-forum | Why does a referenced Alembic hierarchy like /body (Xform) with /body/bodyShape (Mesh) sometimes come into USD as a single /body Mesh prim? |
| c076 | partly | lookup | nvidia-forum | What exactly is a USD stage, and what does it contain? |
| c083 | partly | paraphrase | stackoverflow | My USDZ model has textures A and B on two UV sets and a mask texture on a third. Can I blend A and B with the mask, (A * mask) + (B * (1 - mask)), inside a UsdPreviewSurface material by editing the usda, or does the preview material not support that kind of math? |
| c084 | answerable | paraphrase | stackoverflow | In my usda I reference an .obj file, as in add references = @path/to/model.obj@</Suzanne>, but opening it fails with 'Cannot determine file format for @path/to/model.obj@'. Can USD reference OBJ files directly? |
| c090 | partly | paraphrase | aousd-forum | Is it valid to nest prims under a gprim, for example another Mesh, an Xform or a light beneath a Mesh? What is the reasoning behind the rule? |

## Unanswerable (proposed 18)

| cid | site | question |
| --- | --- | --- |
| c001 | aousd-forum | My UsdUVTexture's file input is a UDIM path like udims/texture.<UDIM>.jpg. Whether the path is relative or absolute, calling .resolvedPath on the asset value always gives an empty string. Is that expected, and how should I resolve UDIM paths? |
| c044 | github-issues | When a stage notice reports a path with resync set to true, what does a resync mean? Should I delete my DCC's object at that path and rebuild it, given that deleting a prim also reports resync? |
| c065 | sidefx-forum | My asset has several variant sets that each change its bounding box. How can I author a correct extentsHint for every combination of variant selections? |
| c073 | nvidia-forum | With a USD PointInstancer (exported from Houdini), how can each instance carry its own color, for example a per-point Cd value, so that a material can tint every instance differently? |
| c085 | stackoverflow | How can I convert a .usdz file to OBJ or Alembic (.abc)? I can only find tools that convert to usdz, not from it. |
| c003 | aousd-forum | Is GfMatrix4d row-major or column-major? After translating by 5 in X, the translation shows up in elements 12-14 rather than 3, 7 and 11, which looks column-major to me. |
| c046 | github-issues | A weaker layer defines a custom float attribute with value 0.8, and a stronger layer overrides it as a double with value 1. Reading it as a float in C++ still returns 0.8, while reading it as a double returns 1.0. How does USD resolve an attribute whose type differs between layers? |
| c066 | sidefx-forum | In Python, Usd.Attribute.Set() fails when the value's type differs from the attribute's type, for example setting a Gf.Quatf on a quath attribute. Is there a way to have USD convert compatible values automatically? |
| c074 | nvidia-forum | I author overrides on prims beneath a referenced asset. On the next update I want to find all existing overrides under that prim so I can remove the stale ones, but GetChildren() and Traverse() on the stage show the composed prims, not which ones I overrode. How do I find the overrides I authored? |
| c086 | stackoverflow | Apple documents USDZ schemas for AR, such as anchoring, that can be authored in the USDZ file itself. Can I read and use those schemas at runtime from Swift? |
| c005 | aousd-forum | I lock layers with SdfLayer.SetPermissionToEdit(False), but the locked state is gone the next time I open the file. Is the permission-to-edit flag stored anywhere in USD, or do I have to reapply it every session? |
| c048 | github-issues | What range and units does UsdPreviewSurface's emissiveColor input expect? Some renderers treat it as physical units (nits) and others as a 0-1 non-physical value. |
| c067 | sidefx-forum | My point instancer uses referenced animated assets with many accessories as prototypes. After instancing, can I randomly hide different accessories on individual instances, or does every variation need its own prototype? |
| c078 | nvidia-forum | I have three cubes with the same rotation: one uses a matrix, one rotateXYZ with Euler angles (5, 10, 15) and one an orient quaternion. How do the rotateXYZ and orient xformOps relate, and in what order are Euler angles applied by rotateXYZ? |
| c087 | stackoverflow | How can I convert an FBX file with morph targets into USD so that the morph targets are kept? Reality Converter and usdzconvert drop them. |
| c009 | aousd-forum | How can I duplicate a prim on a stage with the C++ API, so that the copy is identical except for its name? |
| c049 | github-issues | Does USD support decals, where a face can have several decals in a given drawing order, each with its own UV set, and a decal can span many faces? |
| c096 | sidefx-forum | I sublayer fileA.usd and fileB.usd, mute fileB, and write the composed stage out to myStage.usd. When I load myStage.usd, both layers are active again. Can a layer's muted state be saved in the USD file? |

## Other suggested unanswerable rows (32)

c010, c011, c012, c015, c017, c020, c021, c026, c027, c030, c031, c034, c035, c036, c038, c039, c040, c042, c051, c053, c060, c079, c081, c082, c088, c089, c091, c092, c093, c094, c099, c100
