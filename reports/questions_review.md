# Review of evaluation questions (draft)

Check each answerable question: do the cited lines fully support every expected fact?
Check each unanswerable question: does the corpus really lack the answer? ⚠️ marks items I am unsure of.

## dev (eval/questions.jsonl)

### `payload` — paraphrase

**Q:** Can I leave a heavy scene asset unloaded initially and bring it in later? Which composition arc helps?

- [ ] A payload acts as a deferred reference.
- [ ] It can be loaded or unloaded after the stage is opened.

`docs/intro.rst` L179–184

```rst
and complete scenes. The :ref:`payload arc<glossary:payload>` provides a
"deferred reference" that can be selectively "loaded" (or unloaded) from a
:ref:`glossary:Stage` *after* the stage was initially opened; judicious use
of payloads allows you to structure scenes so that clients can easily manage
"working sets", keeping in memory just the parts of the scene they need for
the task at hand.
```

### `sublayers` — lookup

**Q:** What USD composition arc stacks several layers in a defined order?

- [ ] The subLayers composition arc stacks layers.
- [ ] The composition engine resolves data in the ordered layer stack.

`docs/intro.rst` L170–173

```rst
You can "stack" USD layers together using the :ref:`subLayers composition arc
<glossary:SubLayers>`, and the composition engine will resolve the data
contained in such ordered (nestable) :ref:`"LayerStacks"
<glossary:LayerStack>` similarly to how layers in Photoshop are composed.
```

### `stage` — lookup

**Q:** Which Python calls create a new USD stage on disk and then save its root layer?

- [ ] Use Usd.Stage.CreateNew with the destination path.
- [ ] Call stage.GetRootLayer().Save() to save the root layer.

`docs/tut_helloworld.rst` L19–25

```rst
   .. code-block:: python

      from pxr import Usd, UsdGeom
      stage = Usd.Stage.CreateNew('HelloWorld.usda')
      xformPrim = UsdGeom.Xform.Define(stage, '/hello')
      spherePrim = UsdGeom.Sphere.Define(stage, '/hello/world')
      stage.GetRootLayer().Save()
```

### `attribute` — lookup

**Q:** How does the USD Python tutorial read a sphere's extent attribute?

- [ ] Call sphere.GetAttribute('extent') to obtain the attribute.
- [ ] Call Get() on the attribute to read its value.

`docs/tut_inspect_and_author_props.rst` L41–47

```rst
#. Read the extent attribute on the sphere prim.

   .. code-block:: pycon

      >>> extentAttr = sphere.GetAttribute('extent')
      >>> extentAttr.Get()
      Vt.Vec3fArray(2, (Gf.Vec3f(-1.0, -1.0, -1.0), Gf.Vec3f(1.0, 1.0, 1.0)))
```

### `default-prim` — lookup

**Q:** When a referenced layer has no defaultPrim, what does the referencing client have to provide?

- [ ] Provide the root prim path in the target layer.

`docs/tut_referencing_layers.rst` L14–17

```rst
#. Author the :usda:`defaultPrim` metadata on the layer that you want to
   reference. This is the name of the root prim that will be referenced. If it
   is not authored here, then the referencing client must specify the root prim
   path it wants from the referenced layer. We also want to author a
```

### `add-reference` — lookup

**Q:** What Python call adds a reference to HelloWorld.usda in the Referencing Layers tutorial?

- [ ] Use refSphere.GetReferences().AddReference('./HelloWorld.usda').

`docs/tut_referencing_layers.rst` L89–96

```rst
#. Let's reference in the stage from HelloWorld. Update your script to add
   a reference to "refSphere":

   .. code-block:: python

      refSphere.GetReferences().AddReference('./HelloWorld.usda')
      print(refStage.GetRootLayer().ExportToString())
      refStage.GetRootLayer().Save()
```

### `variant-set` — lookup

**Q:** How does the tutorial create a shadingVariant variant set on a prim in Python?

- [ ] Call GetVariantSets() on the prim.
- [ ] Call AddVariantSet('shadingVariant') on the collection.

`docs/tut_authoring_variants.rst` L66–72

```rst
#. Create a shading variant on the root prim called :usda:`shadingVariant`

   .. code-block:: python

      rootPrim = stage.GetPrimAtPath('/hello')
      vset = rootPrim.GetVariantSets().AddVariantSet('shadingVariant')
      print(stage.GetRootLayer().ExportToString())
```

### `variant-authoring` — lookup

**Q:** How do I author a color change inside the red variant instead of writing a local opinion?

- [ ] Select the red variant with SetVariantSelection.
- [ ] Write the attribute inside GetVariantEditContext().

`docs/tut_authoring_variants.rst` L148–161

```rst
   To author opinions inside the :usda:`red` variant we first select the
   variant, then use a :python:`Usd.EditContext`.  This directs editing into
   the variant.
   
   .. code-block:: python

      vset.SetVariantSelection('red')
      with vset.GetVariantEditContext():
          colorAttr.Set([(1,0,0)])

      print(stage.GetRootLayer().ExportToString())

   If we just invoked :python:`colorAttr.Set()` without using the variant edit
   context, we would write a *local* opinion; specifically the same opinion we
```

### `outside-pyro` — unanswerable

**Q:** What voxel size and dissipation should I set for Pyro smoke in my Houdini shot?

- [ ] Confirmed: no answer in the corpus

### `outside-performance` — unanswerable

**Q:** How many gigabytes of video memory will the payload for our studio's city scene consume on my workstation?

- [ ] Confirmed: no answer in the corpus

### `timecodes-per-second` — lookup

**Q:** Which layer metadata scales TimeCodes to real-time seconds?

- [ ] timeCodesPerSecond scales TimeCodes to seconds.
- [ ] It is read from the root layer or the session layer.

`docs/glossary.rst` L3543–3546

```rst
For a composed scene, :ref:`TimeCode <usdglossary-timecode>` coordinate values 
from :ref:`animated values <usdglossary-animatedvalue>` are scaled to real-time 
seconds by the root layer's (or session layer's) :usda:`timeCodesPerSecond` 
metadata. 
```

### `expression-targets` — lookup

**Q:** Where in a USD scene can variable expressions currently be used?

- [ ] Variable expressions can be used in asset paths, including sublayer, reference and payload paths.
- [ ] Variable expressions can be used in variant selections.

`docs/user_guides/variable_expressions.rst` L19–23

```rst
Variable expressions can currently be used in:

- Asset paths (including sublayer, reference, and payload asset paths as well as 
  asset-valued attributes and metadata). 
- Variant selections.
```

### `indexed-primvars` — lookup

**Q:** What problem do indexed primvars solve, and what is a common example?

- [ ] Indexed data is referred to by index instead of repeating elements.
- [ ] Indexing reduces memory usage.
- [ ] Surface normals shared by several vertices are a common use case.

`docs/user_guides/primvars.rst` L451–456

```rst
Primvars support *indexed data*, so data can be referred to by index rather 
than repeating the full elements, thereby reducing memory usage. A common 
use-case is using a primvar to describe surface normals for a Mesh, where 
several vertices use the same normal vector. In this scenario, it would be 
much more efficient to use primvar indices rather than duplicating the normals 
in the primvar array. 
```

### `vertex-primvar` — lookup

**Q:** How many elements does a vertex-interpolated primvar need on a Mesh, and in what order?

- [ ] Provide one element for each point of the mesh.
- [ ] The order matches the Mesh points array.

`docs/user_guides/primvars.rst` L123–125

```rst
For Mesh prims, you'll provide a primvar array with one element for each 
point of the mesh, with the order of the primvar array matching the order 
of the Mesh :mono:`points` array.
```

### `face-varying` — lookup

**Q:** What does faceVarying primvar interpolation let me specify on a polygon mesh?

- [ ] faceVarying allows different elements for each face-vertex.
- [ ] Bilinear interpolation is used between the elements.

`docs/user_guides/primvars.rst` L296–299

```rst
For polygons and subdivision surfaces, faceVarying interpolation allows you to 
specify different :ref:`elements <primvar_element_size>` for each face-vertex.
Bilinear interpolation (with additional rules for subdivision surfaces, see 
below) is used for interpolation between the elements. faceVarying interpolation 
```

### `layer-offset-compose` — lookup

**Q:** If A references B with a time scale of 2.0 and B references C with 3.5, what time scale applies to C's data at A?

- [ ] Layer offsets compose.
- [ ] The total time scale is 7.0.

`docs/glossary.rst` L1555–1563

```rst
`Composition arcs <#usdglossary-compositionarcs>`_ such as `References
<#usdglossary-references>`_ and `SubLayers <#usdglossary-sublayers>`_ can
include an offset and scaling of time to be applied during attribute `value
resolution <#usdglossary-valueresolution>`_ for all data composed from the
target layer. We call this a *Layer Offset*, embodied in
:usdcpp:`SdfLayerOffset`.  Layer offsets compose, so that if **A** references
**B** with a time-scale of 2.0 and **B** references **C** with a time-scale of
3.5, then data resolved at **A** whose source is **C** will have a total
time-scale of 7.0 applied to it.
```

### `layer-offset-scale` — lookup

**Q:** In the transformations tutorial, what does a layer offset scale of 0.25 do to the referenced top's animation?

- [ ] A scale of 0.25 plays the animation back at 4x the rate.

`docs/tut_xforms.rst` L495–498

```rst
Here we reference the above animation in 3 times, adding a different +X
translation to each. The first top has no layer offset; the second has a +96
frame offset (causing it to be 180 degrees out of phase), and the third top has
a scale of 0.25 (causing its animation to play back at 4x the rate).
```

### `attribute-block` — lookup

**Q:** How do I block the value of an attribute, and can the block be overridden?

- [ ] Author an overriding opinion of None.
- [ ] UsdAttribute::Block() authors the block.
- [ ] A stronger opinion can override the block.

`docs/glossary.rst` L372–376

```rst
Similarly to how `prims can be deactivated <#usdglossary-active-inactive>`_
through composing overriding opinions, the value that an attribute produces can
be **blocked** by an overriding opinion of :usda:`None`, which can be authored 
using :usdcpp:`UsdAttribute::Block() <UsdAttribute::Block>`. A block itself can, 
of course be overridden by an even stronger opinion. 
```

### `jemalloc` — lookup

**Q:** Which memory allocator does Pixar use with USD, and how can I force it on a third-party application on Linux?

- [ ] Pixar uses jemalloc.
- [ ] Use the LD_PRELOAD environment variable to force a different allocator.

`docs/maxperf.rst` L40–59

```rst
neither of which hold up very well under high thread-count. At Pixar,
we have been successfully and stably using `jemalloc <http://jemalloc.net/>`_,
which has the following virtues:

    * Outperforms glibc consistently for USD stage loading and imaging through
      Hydra by a factor of **2x** on a 16 core Intel workstation

    * Does an outstanding job of returning freed memory to the kernel

In the `Advanced Build Configuration
<https://github.com/PixarAnimationStudios/OpenUSD/blob/release/BUILDING.md>`_
document, you can find instructions for how to build USD linked against a
third-party malloc package such as jemalloc. If you are using USD in a third
party application as an embedded plugin, you can force the application to use a
different allocator on Linux by using the :envvar:`LD_PRELOAD` environment
variable. For example:

.. code-block:: console

   > env LD_PRELOAD=/path/to/jemalloc.so thirdPartyApplication
```

### `pre-post-visit` — lookup

**Q:** How can a Python traversal visit each prim both before and after its children?

- [ ] Use Usd.PrimRange.PreAndPostVisit.
- [ ] IsPostVisit() tells whether the current visit is the post-visit.

`docs/tut_traversing_stage.rst` L42–48

```rst
#. For more involved traversals, the :python:`Usd.PrimRange()` exposes pre- and
   post-order prim visitations.

   .. code-block:: pycon

      >>> primIter = iter(Usd.PrimRange.PreAndPostVisit(usdviewApi.stage.GetPseudoRoot()))
      >>> for x in primIter: print(x, primIter.IsPostVisit())
```

### `expression-defined` — lookup

**Q:** What does the defined() function in a USD variable expression return when it is given several variable names?

- [ ] It returns true only if all listed variables are defined.
- [ ] Variable names must be simple strings, not variable expressions.

`docs/user_guides/variable_expressions.rst` L285–290

```rst
If <variable name> is defined in the composed set of expression 
variables visible to the layer where the expression is authored, return 
:usda:`true`, otherwise return :usda:`false`. This function can take multiple 
variable names. All listed variable names must be defined for this function to 
return true. Note that variable names must be provided as simple strings -- you 
cannot use a string that contains a variable expression with this function.
```

### `usda-encoding` — lookup

**Q:** What text encoding does the .usda format use, and does USD normalize Unicode in identifiers?

- [ ] The .usda format encodes text as UTF-8.
- [ ] USD does not enforce or apply Unicode normalization.
- [ ] NFC is preferred when creating new tokens and paths.

`docs/usdfaq.rst` L136–146

```rst
The :filename:`.usda` file format encodes text as UTF-8.

As of the 24.03 release, USD extends UTF-8 support to path and metadata 
identifiers.

USD does not enforce or apply Unicode normalization. As an example, the 
second letter in München can be represented in UTF-8 by a single code point 
(the code point for ü) or two code points (u with an umlaut modifier) -- to USD, 
these two representations of München are distinct. While USD does not enforce a 
normalization form, Unicode "Normalization Form C" (NFC) is preferred when 
creating new tokens and paths.
```

### `reversible-hide` — paraphrase

**Q:** How can I remove a prim and everything below it from the composed scene in a way that a stronger layer can undo?

- [ ] Make the prim inactive with UsdPrim::SetActive(false).
- [ ] Deactivation is a non-destructive, reversible prim deletion.
- [ ] Descendants of an inactive prim are not composed.
- [ ] A stronger layer can override active back to true.

`docs/glossary.rst` L43–59

```rst
*Activation* is a `metadatum <#usdglossary-metadata>`_/behavior of `prims
<#usdglossary-prim>`_ that models a "non destructive and reversible prim
deletion" from a `stage <#usdglossary-stage>`_ . Prims are active by default,
which means they and their active children will be `composed
<#usdglossary-composition>`_ and visited by `stage traversals
<#usdglossary-stagetraversal>`_. However, by making a prim *inactive* by calling
:usdcpp:`UsdPrim::SetActive(false) <UsdPrim::SetActive>`,
we prevent the prim itself from being visited by default traversals, and we
also prevent the prim's descendant prims from even being composed on the stage,
which makes *deactivation* a useful tool for pruning unneeded scene description
for scalability and complexity management.

In the following example, the prim at `path <#usdglossary-path>`_
:sdfpath:`/Parent` has been deactivated, so :sdfpath:`/Parent/Child1` and other
descendants will not be composed. However, :sdfpath:`/Parent`'s :usda:`active`
metadatum can be overridden to *true* in a stronger layer, which would cause
:sdfpath:`/Parent/Child1` and etc. to compose onto the stage.
```

### `lightweight-asset-open` — paraphrase

**Q:** Our big set takes minutes to open because every asset pulls in all its geometry. How should assets be packaged so artists can browse the set quickly?

- [ ] Use a payload arc, which acts as a deferred reference.
- [ ] Publish a lightweight interface file that holds a payload to the full geometry and shading.
- [ ] The stage can be opened unloaded.

`docs/maxperf.rst` L117–131

```rst
When dealing with very large scenes, many important pipeline tasks can be
accomplished without knowing about or processing all of the geometry and shading
on many (or all!) of the assets in the scene. These tasks can therefore be
accomplished much more quickly if we can get a view of the scene that does not
populate those aspects of the referenced assets. USD provides a composition arc
called a :ref:`Payload <glossary:Payload>` that is essentially a
"deferred reference". It allows us to structure scenes so that we can open a
:ref:`Stage <glossary:Stage>` "unloaded", meaning that we USD will populate the stage
only "up to" the payload arcs. One effective way to make use of this is to
publish each of your "model assets" such that the file that gets referenced into
assemblies and shots is a very lightweight description of the model's
"interface" (e.g. its :ref:`AssetInfo <glossary:AssetInfo>`,
:ref:`VariantSets <glossary:VariantSet>`, rest bounding box), and
a payload arc to a separate file that pulls in the complete geometric and
shading description of the asset.
```

### `working-set` — paraphrase

**Q:** Can I keep most of a huge stage out of memory and fully compose only the assets my current task needs?

- [ ] Payloads let a client load or unload the scene description they target.
- [ ] Unloading recursively unloads payloads beneath the prim.
- [ ] Clients can craft working sets that compose only the parts needed, saving time and memory.

`docs/glossary.rst` L1817–1827

```rst
The `Payload arc <#usdglossary-payload>`_ provides a "deferred reference"
behavior. Wherever a Stage contains at least one Payload (payloads can be
list-edited and chained), the client has the ability to **Load** (compose) all
the scene description targeted by the Payload, or to **Unload** the Payloads and
all their scene description, recomposing all prims beneath the payloaded-prim,
recursively unloading *their* payloads, should they possess any. We generally
associate payloads with "model assets", which provides us with payloads, and
therefore "load points" at all the leaves of the `Model Hierarchy
<#usdglossary-modelhierarchy>`_. This organization allows clients to craft
"working sets" of a Stage, fully composing only the parts of the scene needed
for a given task, saving time and memory for the operation.
```

### `active-vs-visibility` — comparison ⚠️

**Q:** What is the difference between deactivating a prim and making it invisible?

**Unsure:** Two sources; confirm the glossary does not contrast the two directly elsewhere.

- [ ] Deactivation prevents the prim's descendants from being composed on the stage.
- [ ] Inactive prims are skipped by default traversals.
- [ ] Invisibility is a visibility attribute value that prunes the subtree from rendering.

`docs/glossary.rst` L43–53

```rst
*Activation* is a `metadatum <#usdglossary-metadata>`_/behavior of `prims
<#usdglossary-prim>`_ that models a "non destructive and reversible prim
deletion" from a `stage <#usdglossary-stage>`_ . Prims are active by default,
which means they and their active children will be `composed
<#usdglossary-composition>`_ and visited by `stage traversals
<#usdglossary-stagetraversal>`_. However, by making a prim *inactive* by calling
:usdcpp:`UsdPrim::SetActive(false) <UsdPrim::SetActive>`,
we prevent the prim itself from being visited by default traversals, and we
also prevent the prim's descendant prims from even being composed on the stage,
which makes *deactivation* a useful tool for pruning unneeded scene description
for scalability and complexity management.
```

`docs/glossary.rst` L4236–4247

```rst
*Visibility* is a builtin attribute of the :usdcpp:`UsdGeomImageable` base
schema, and models the simplest form of "pruning" invisibility that is
supported by most DCC apps. Visibility can take on two possible token string
values: 

    * **inherited** (the fallback value if the attribute is not authored)
    * **invisible** 

If the `resolved value <#usdglossary-valueresolution>`_ is **invisible**, then
neither the prim itself nor any prims in the subtree rooted at the prim should
be rendered - this is what we mean by "pruning invisibility", since invisible
subtrees are definitively pruned in their entirety. If the resolve value is
```

### `constant-vs-uniform` — comparison

**Q:** For a mesh, how does constant primvar interpolation differ from uniform interpolation?

- [ ] Constant uses a single element across the whole prim, still authored as an array.
- [ ] Uniform uses one element for each face of the mesh.

`docs/user_guides/primvars.rst` L39–41

```rst
A :ref:`single element <primvar_element_size>` is specified across the entire 
prim surface/volume. Note that you still need to provide an array (that contains 
a single element) for the primvar.
```

`docs/user_guides/primvars.rst` L76–78

```rst
:ref:`One element <primvar_element_size>` remains constant for each patch 
segment of the prim's surface/volume. For a mesh prim, provide an array with a 
single element for each face of the mesh. For a curve prim, provide an array 
```

### `sublayers-vs-references` — comparison

**Q:** When combining layers, should I prefer sublayers or references, and what can references do that sublayers cannot?

- [ ] Prefer sublayering if it satisfies the requirements.
- [ ] Sublayering gives the most compact runtime structures and efficient value resolution.
- [ ] References can remap prims into a different namespace.

`docs/usdfaq.rst` L281–303

```rst
**If it satisfies your requirements, prefer sublayering over referencing.**

Sublayering has the following advantages:

    * Sublayering is the simplest :ref:`Composition Arc <glossary:Composition Arcs>` 
      and results in the most compact runtime data structures and efficient
      :ref:`glossary:Value Resolution`.

    * Layers combined via sublayering can easily participate in 
      :usdcpp:`UsdStage Layer Muting <UsdStage::MuteLayer>`.

    * Choosing layers to edit via :ref:`Edit Targets <glossary:EditTarget>`
      is most straightforward for layers combined via sublayering.

**What requirements might make SubLayering inappropriate?**

    * If the layers you need to combine to do not share the same namespace,
      sublayering will simply "overlay" the different namespaces without any
      possibility of renaming parts of the namespace. By contrast, references
      allow you to remap specific prims into a different namespace. For example,
      the prim :sdfpath:`/Bob` in the file :filename:`Bob.usd` can be
      *renamed* to :sdfpath:`/Bob_1` as it is referenced onto the prim
      :sdfpath:`/Characters/Bob_1` in the file :filename:`lineup.usd`.
```

### `gaussian-splats` — unanswerable

**Q:** Which OpenUSD schema should I use to store 3D Gaussian splats, and how are the splat attributes laid out?

- [ ] Confirmed: no answer in the corpus

### `docker-usdview` — unanswerable

**Q:** Which official Docker image should I use to run usdview on a headless server?

- [ ] Confirmed: no answer in the corpus

### `sign-usdz` — unanswerable

**Q:** How do I digitally sign a usdz package with a certificate so that iOS can verify it?

- [ ] Confirmed: no answer in the corpus

### `nucleus-live-sync` — unanswerable ⚠️

**Q:** How do I set up live sync of USD layers through an Omniverse Nucleus server?

**Unsure:** usd_products.rst mentions Omniverse as a product; confirm it says nothing about Nucleus or live sync.

- [ ] Confirmed: no answer in the corpus

## heldout (eval/heldout.jsonl)

### `usdz-zip` — lookup

**Q:** Are compression or encryption allowed inside a usdz zip archive?

- [ ] A usdz package is a zero-compression zip archive.
- [ ] A usdz package is unencrypted.

`docs/spec_usdz.rst` L93–94

```rst
A usdz package is a **zero compression, unencrypted** zip archive. We reserve
the ability to relax this constraint in the future, but consider it unlikely.  
```

### `primvar-modes` — lookup

**Q:** Which primvar interpolation modes does USD support?

- [ ] USD supports five interpolation modes.
- [ ] The modes are constant, uniform, varying, vertex and faceVarying.

`docs/user_guides/primvars.rst` L21–27

```rst
USD currently supports five primvar interpolation modes:

* constant
* uniform
* varying
* vertex
* faceVarying
```

### `languages` — lookup

**Q:** Which programming languages can I use with USD?

- [ ] USD is a set of C++ libraries.
- [ ] USD has Python bindings for scripting.

`docs/usdfaq.rst` L32–32

```rst
USD consists of a set of C++ libraries with Python bindings for scripting.
```

### `stage-traverse` — lookup

**Q:** Which Python call yields the prims of a stage in depth-first order?

- [ ] Usd.Stage.Traverse() is a generator.
- [ ] It yields prims in depth-first traversal order.

`docs/tut_traversing_stage.rst` L26–27

```rst
   The simplest place to start is with :python:`Usd.Stage.Traverse()`; a
   generator which yields prims from the stage in depth-first-traversal order.
```

### `usdcat-to-text` — lookup

**Q:** Which usdcat option converts a binary .usd file to the text format while keeping the .usd extension?

- [ ] Use usdcat with --usdFormat usda.
- [ ] Write the output with --out file.usd.

`docs/usdfaq.rst` L155–166

```rst
:ref:`usdcat <toolset:usdcat>` can be used to convert files between file
formats. With plain, :filename:`.usd` files, you can change them using the
:option:`--usdFormat` option. 

.. note::

  Although you can specify :option:`--usdFormat usdc`, it is not necessary, since
  the :option:`--out file.usd` argument will, by default choose the usdc format.

.. code-block:: sh

   $ usdcat file.usd --out file.usd --usdFormat usda
```

### `session-layer-save` — lookup

**Q:** Does UsdStage::Save write the stage's session layer, and how strong is that layer?

- [ ] The session layer is the strongest layer in the root LayerStack.
- [ ] UsdStage::Save does not save the session layer.

`docs/glossary.rst` L3201–3214

```rst
Each `UsdStage <#usdglossary-stage>`_ can be created with a *session layer* that
provides for "scratch space" to configure, override, and experiment with the
data contained in files backing the stage. If requested or provided at stage
creation-time, a session layer participates fully in the stage's `composition
<#usdglossary-composition>`_, as the strongest layer in the stage's `Root
LayerStack <#usdglossary-rootlayerstack>`_, and can possess its own `SubLayers
<#usdglossary-sublayers>`_. Session layers generally embody "application state",
and, if saved, would be saved as part of application state rather than as part 
of the data set they modify. :ref:`toolset:usdview` creates a sesssion layer, 
into which are targeted all `VariantSet <#usdglossary-variantset>`_ selections,
`vis/invis <#usdglossary-visibility>`_ opinions, and `activation/deactivation
<#usdglossary-active-inactive>`_ operations provided by the GUI. In keeping with
the view of session-layer as application state rather than asset data,
:usdcpp:`UsdStage::Save` **does not save its stage's session layer(s)**.
```

### `collection-modes` — lookup

**Q:** What are the two ways to specify a collection's membership, and can they be combined?

- [ ] Relationship-mode uses target-based include and exclude rules.
- [ ] Expression-mode uses pattern-based expressions.
- [ ] A collection cannot mix the two modes.
- [ ] The mode attribute selects the mode.

`docs/user_guides/collections_and_patterns.rst` L22–31

```rst
A collection's membership is specified in one of two ways. The first way uses
target-based rules to specify which objects are included (and excluded) from
the collection. Collections configured this way are considered to be in 
**relationship-mode**. A second way of specifying membership uses an 
expression-based syntax to match objects to be included in the collection. 
Collections configured this way are **pattern-based collections** and the 
collection is considered to be in **expression-mode**. Note that you cannot mix 
collection configurations. Collections can be configured to work in 
relationship-mode or expression-mode, but not a mix of the two. You can 
specify which mode a collection should use via the ``mode`` attribute.
```

### `kind-model-abstract` — lookup

**Q:** Can I assign the kind 'model' directly to a prim?

- [ ] model is an abstract kind.
- [ ] model should not be assigned as any prim's kind.

`docs/glossary.rst` L1479–1481

```rst
    * `model <#usdglossary-model>`_ - base class for all model kinds. **"model"
      is considered an abstract type and should not be assigned as any prim's
      kind.** 
```

### `namespace-edit-ops` — lookup

**Q:** Which operations does a USD namespace edit currently support?

- [ ] Namespace edits can delete a composed prim or property.
- [ ] Namespace edits can move, rename or reparent a composed prim or property.

`docs/user_guides/namespace_editing.rst` L9–11

```rst
A namespace edit is an operation that removes or changes the namespace path of 
a **composed** prim or property on a stage. Edit operations currently include 
deleting and moving (renaming and/or reparenting) a composed prim or property.
```

### `rename-to-usd` — lookup

**Q:** Can I turn Sphere.usda into a .usd file without running a converter?

- [ ] A .usd file can be text or binary.
- [ ] USD detects the underlying format when it opens a .usd file.
- [ ] Renaming the file is enough.

`docs/tut_converting_between_layer_formats.rst` L22–25

```rst
A :filename:`.usd` file can be either a text or binary format file. When USD
opens a :filename:`.usd` file, it detects the underlying format and handles the
file appropriately. You can convert any :filename:`.usda` or :filename:`.usdc`
file to a :filename:`.usd` file simply by renaming it.  For example:
```

### `instanceable-condition` — lookup

**Q:** When does a prim with instanceable = true actually become an instance?

- [ ] The prim must also have one or more direct composition arcs.
- [ ] Only the composed value of instanceable matters.

`docs/glossary.rst` L1255–1262

```rst
:usdcpp:`UsdPrim::SetInstanceable`. If :usda:`instanceable = true` on a prim,
then the prim will become an instance of an implicit prototype when composed
on a `stage <#usdglossary-stage>`_, if and only if the prim also contains one
or more direct `composition arcs. <#usdglossary-compositionarcs>`_ It does
not matter whether :usda:`instanceable` is authored in a referenced layer (on
the prim being referenced) or in the layer (or a super-layer) in which the
reference is authored: only the `composed value
<#usdglossary-valueresolution>`_ on the prim matters. See `Instancing
```

### `broadcast-edit` — paraphrase

**Q:** How do I make one non-destructive edit that applies to a whole family of similar objects on a stage?

- [ ] Use the inherits composition arc.
- [ ] Opinions on the source prim broadcast to every prim that inherits it.

`docs/glossary.rst` L1126–1132

```rst
*Inherits* is a `composition arc <#usdglossary-compositionarcs>`_ that addresses
the problem of adding a single, non-destructive edit (override) that can affect
a whole *class* of distinct objects on a `stage <#usdglossary-stage>`_. Inherits
acts as a non-destructive "broadcast" operator that applies opinions authored
on one prim to every other prim that inherits the "source" prim; not only do
property opinions broadcast over inherits arcs - **all** scene description,
hierarchically from the source, inherits. Consider the following example:
```

### `helper-geometry-in-renders` — paraphrase

**Q:** How do I keep rig controls and other helper geometry out of final renders but still show them in an interactive viewer on request?

- [ ] Set the prim's purpose to guide.
- [ ] Guide geometry is included only when an application is asked to show guides.

`docs/glossary.rst` L2468–2475

```rst
The fallback purpose, ***default*** indicates that a prim has "no special
purpose" and should generally be included in all traversals. Subtrees rooted at
a prim with purpose ***render*** should generally only be included when
performing a "final quality" render. Subtrees rooted at a prim with purpose
***proxy*** should generally only be included when performing a lightweight
proxy render (such as OpenGL). Finally, subtrees rooted at a prim with purpose
***guide*** should generally only be included when an interactive application
has been explicitly asked to "show guides".
```

### `move-without-touching-source` — paraphrase

**Q:** How can I rename a prim that comes from another department's referenced asset without changing their file?

- [ ] Use namespace editing.
- [ ] Namespace editing adds a relocates arc when needed.
- [ ] The source of the composition arc is not modified.

`docs/user_guides/namespace_editing.rst` L16–28

```rst
Use namespace editing to easily and safely delete or move prims and properties
across the :ref:`LayerStack <usdglossary-layerstack>`. Namespace editing handles 
edits for objects composed from multiple layers and handles changing 
:ref:`EditTargets <usdglossary-edittarget>` or fixing paths targeting the 
edited objects, automatically.

Namespace also provides non-destructive editing of prims defined across 
composition arcs by adding the **relocates** composition arc if needed.
By using relocates, namespace editing ensures non-destructive edits by *not*
modifying the source of a composition arc. This is necessary for workflows where
you might not be able to make changes to the source of the composition 
arc directly (e.g. you're referencing prims from assets maintained by a 
different department that are also being referenced elsewhere).
```

### `switchable-asset-root` — paraphrase

**Q:** I want one scene file whose reference paths point to a different asset folder depending on a single setting. What USD feature fits?

- [ ] Use variable expressions.
- [ ] Expression variables are defined in the expressionVariables layer metadata.

`docs/user_guides/variable_expressions.rst` L9–17

```rst
Variable expressions are specially formatted strings that contain expressions 
that USD will evaluate at runtime. The expressions can contain variable data 
and logic used to dynamically create or change values in your USD scene. Use
variable expressions to easily configure your scene without having to make
extensive scene data modifications. 

Variable expressions use named expression variables that can be easily 
defined and changed in layer metadata. Expression variables are defined in a 
"expressionVariables" dictionary metadata field in a layer. 
```

### `over-vs-def` — comparison

**Q:** What is the difference between an 'over' and a typeless 'def' for a prim?

- [ ] def expects a type to be provided by the time the stage is composed.
- [ ] over layers opinions onto a prim only if something else defines it.
- [ ] UsdPrim::GetChildren skips prims that are only over.

`docs/usdfaq.rst` L625–642

```rst
**Answer** : When you *def* a prim, you're providing more information to the
system than when you *over* a prim.

    * **def** means "Even though I may not be declaring a typed prim in this
      layer, by the time the :usdcpp:`UsdStage` has finished composing, I
      **expect** a type to have been provided by referenced/layered scene
      description" (in the example, presumably the type would be provided by the
      layer targeted by the *payload* arc.

    * **over** means "If some referenced layer happens to define this prim, then
      layer the information I contain onto it; but if not, just consider this
      information ancillary"

This distinction is actually used in the Usd core to define, for e.g., default
stage traversal behavior, as :usdcpp:`UsdPrim::GetChildren`
only iterates over a prim's *defined* children (regardless of whether they
possess a type in the current view of the stage), skipping prims that are just
*over*.
```

### `specializes-vs-inherits` — comparison

**Q:** How does the specializes arc differ from inherits?

- [ ] Opinions on a specialized prim are always stronger than opinions on the base prim in any referencing context.
- [ ] The key difference is the relative strength of referenced opinions versus inherited or specialized opinions.

`docs/glossary.rst` L3227–3237

```rst
*Specializes* is a `composition arc <#usdglossary-compositionarcs>`_ that allows
a *specialized* prim to be continuously refined from a *base* prim, through
unlimited levels of referencing. A specialized prim will contain all of the
scene description contained in the base prim it specializes (including the
entire namespace hierarchy rooted at the base prim), but any opinion expressed
directly on the specialized prim will always be stronger than any opinion
expressed on the base prim, **in any referencing context**. In behavior,
specializes is very similar to `inherits <#usdglossary-inherits>`_, with the
key difference being the relative strength of referenced opinions vs
"inherited/specialized" opinions, which leads to very different uses for the
two.
```

### `usda-vs-usdc` — comparison

**Q:** When should I use .usda text files and when the binary usdc format?

- [ ] usda is a good choice for small files that mostly reference or sublayer other files.
- [ ] usdc opens faster and uses much less memory for larger files.
- [ ] A new someFile.usd is created as usdc by default.

`docs/maxperf.rst` L64–75

```rst
:filename:`.usda` text files can be a good choice for small files
that primarily reference/subLayer other files together, such as the top-level
"asset interface" file that defines a :ref:`Model <glossary:Model>`, provides
its :ref:`AssetInfo <glossary:AssetInfo>`, declares its :ref:`VariantSets
<glossary:VariantSet>`, and contains a :ref:`payload arc <glossary:Payload>`
to the asset's contents. But for files that contain more than a few small
definitions or overrides, the binary :ref:`"usdc" format <glossary:Crate File
Format>` will open faster and consume substantially much less memory while
held open (a :ref:`UsdStage <glossary:Stage>` keeps open all the layers that
participate in a composition). You should not need to exert any extra effort
to get this behavior since creating a new layer or stage with a filename
:filename:`someFile.usd` will, by default, create a usdc file.
```

### `android-usdz` — unanswerable

**Q:** Which Android API loads a usdz file into an AR scene?

- [ ] Confirmed: no answer in the corpus

### `aousd-fee` — unanswerable

**Q:** How much does an annual AOUSD membership cost for a mid-sized studio?

- [ ] Confirmed: no answer in the corpus

### `karma-samples` — unanswerable

**Q:** How many pixel samples should I set in Karma XPU when rendering a USD scene from Houdini Solaris?

- [ ] Confirmed: no answer in the corpus

### `storm-vram` — unanswerable ⚠️

**Q:** How much GPU memory does Storm need to display a 10-million-polygon USD scene in usdview?

**Unsure:** ref_performance_metrics.rst lists test-machine RAM and timings; confirm it gives no VRAM requirement.

- [ ] Confirmed: no answer in the corpus

### `webgpu-viewer` — unanswerable

**Q:** How do I render a USD stage in a web browser with WebGPU?

- [ ] Confirmed: no answer in the corpus

### `perforce-usdview` — unanswerable

**Q:** How do I check out USD layers from a Perforce depot directly inside usdview?

- [ ] Confirmed: no answer in the corpus
