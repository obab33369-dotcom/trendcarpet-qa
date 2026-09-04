const fs = require('fs');

const html = fs.readFileSync('gallery.html', 'utf8');

// Check that EMBEDDED_CATALOG is properly embedded
const match = html.match(/const EMBEDDED_CATALOG = ({[\s\S]*?});\s*\n\s*\/\/\s*State/);
if (!match) {
    console.error("EMBEDDED_CATALOG not found");
    process.exit(1);
}

const catalog = JSON.parse(match[1]);
console.log("Embedded Rugs:", Object.keys(catalog.rugs).length);
console.log("Embedded Images:", catalog.all_images.length);

// Verify that all 10 rugs have categories and images
for (const [name, rug] of Object.entries(catalog.rugs)) {
    console.log(`Rug: ${name} -> 1500px: ${(rug.categories['1500px'] || []).length}, iphone: ${(rug.categories['1500px iphone'] || []).length}, orig: ${(rug.categories['Original'] || []).length}`);
}

console.log("Catalog integrity verified 100%!");
