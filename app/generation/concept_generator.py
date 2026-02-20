
def generate_concepts(brand_id, sku_id, channel, count=10):
    """Return `count` creative concepts (stub: hardcoded). Each is a dict matching CreativeConcept."""
    stub_concepts = [
        {
            "creative_id": f"{brand_id}-gen-1",
            "sku_id": sku_id,
            "channel": channel,
            "hook": "Why is your dog scratching? Try this.",
            "angle": "Relief without the vet bill",
            "script": "Our soft chews support skin comfort. Real ingredients, no fillers. Worth a try.",
            "shot_list": "1. Dog scratching. 2. Owner with chews. 3. Happy dog.",
            "cta": "Try risk-free",
        },
        {
            "creative_id": f"{brand_id}-gen-2",
            "sku_id": sku_id,
            "channel": channel,
            "hook": "Stop the scratch cycle in 2 weeks",
            "angle": "Vet-style support at home",
            "script": "These chews help promote healthy skin. No mystery ingredients. Just what your dog needs.",
            "shot_list": "1. Before/after. 2. Chew close-up. 3. Dog resting.",
            "cta": "Shop now",
        },
        {
            "creative_id": f"{brand_id}-gen-3",
            "sku_id": sku_id,
            "channel": channel,
            "hook": "POV: You finally found something that works",
            "angle": "Real results from real ingredients",
            "script": "After trying everything, these chews actually helped. Supports skin health without the vet visit.",
            "shot_list": "1. UGC style. 2. Showing chews. 3. Dog relaxed.",
            "cta": "Get 20% off",
        },
    ]
    return stub_concepts[: max(1, count)]
