// Builds a depth-first, parent-before-children ordering from a flat
// category list, so a plain dropdown can render indentation instead of a
// full nested tree widget. Categories whose parent isn't in the list
// (shouldn't happen — every parent_id is validated server-side against the
// same org — but defends against a stale/partial fetch) are treated as roots.
export function flattenCategoryTree(categories) {
  const byParent = new Map();
  for (const category of categories) {
    const key = category.parent_id ?? null;
    if (!byParent.has(key)) byParent.set(key, []);
    byParent.get(key).push(category);
  }
  for (const list of byParent.values()) {
    list.sort((a, b) => a.name.localeCompare(b.name));
  }

  const knownIds = new Set(categories.map((c) => c.id));
  const result = [];

  const visit = (parentId, depth) => {
    for (const category of byParent.get(parentId) ?? []) {
      result.push({ ...category, depth });
      visit(category.id, depth + 1);
    }
  };

  visit(null, 0);
  // Orphans: parent_id set but not found among knownIds (fetch was
  // paginated/partial). Show them as roots rather than dropping them.
  for (const category of categories) {
    if (category.parent_id !== null && !knownIds.has(category.parent_id)) {
      result.push({ ...category, depth: 0 });
    }
  }
  return result;
}
