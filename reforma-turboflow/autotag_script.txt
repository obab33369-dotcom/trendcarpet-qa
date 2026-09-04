/**
 * Reforma Automation - TurboFlow Auto-Tagging Console Script
 * 
 * INSTRUCTIONS:
 * 1. Open Google Labs Flow in Chrome.
 * 2. Click the TurboFlow extension icon to open its interface.
 * 3. Right-click anywhere inside the TurboFlow popup/window and select "Inspect" (Undersök).
 * 4. This opens Chrome DevTools. Click on the "Console" tab at the top.
 * 5. Paste this entire script into the console and press Enter.
 * 6. Watch all your uploaded images get tagged automatically in seconds!
 */

async function autoTagTurboFlow() {
  console.log("🚀 Starting TurboFlow Auto-Tagging script...");
  
  // Helper to generate the exact short tag matching get_short_tag in prompt generator
  function getShortTag(filename) {
    const encoder = new TextEncoder();
    const bytes = encoder.encode(filename);
    const decoder = new TextDecoder('windows-1252');
    let corrupted = decoder.decode(bytes).toLowerCase();
    
    let lastDot = corrupted.lastIndexOf('.');
    let base = lastDot !== -1 ? corrupted.substring(0, lastDot) : corrupted;
    
    let cleaned = '';
    for (let i = 0; i < base.length; i++) {
      let c = base[i];
      if (/[a-z0-9_-]/.test(c)) {
        cleaned += c;
      } else {
        cleaned += '-';
      }
    }
    let collapsed = cleaned.replace(/-+/g, '-');
    let truncated = collapsed.substring(0, 20).replace(/^-+|-+$/g, '');
    return `@${truncated}`;
  }

  // 1. Find all elements that look like image filenames (e.g. starting with digits_ or ending in image extension)
  const fileElements = Array.from(document.querySelectorAll('*')).filter(el => {
    const text = el.textContent ? el.textContent.trim() : '';
    const isFile = /\.(png|webp|jpg|jpeg)$/i.test(text) || /^\d+_/.test(text);
    if (!isFile) return false;
    
    // Ensure it's the deepest element in the DOM tree that contains this specific name
    return !Array.from(el.querySelectorAll('*')).some(child => {
      const childText = child.textContent ? child.textContent.trim() : '';
      return /\.(png|webp|jpg|jpeg)$/i.test(childText) || /^\d+_/.test(childText);
    });
  });
  
  console.log(`📸 Found ${fileElements.length} image elements matching the ID format.`);
  
  if (fileElements.length === 0) {
    console.error("❌ No image elements found! Make sure you are on the 'Library' tab in TurboFlow and have uploaded the images.");
    return;
  }
  
  let successCount = 0;
  
  for (const fileEl of fileElements) {
    const filename = fileEl.textContent.trim();
    const tagToApply = getShortTag(filename);
    
    // 2. Find the card container by walking up the DOM tree
    let cardContainer = fileEl.parentElement;
    let tagButton = null;
    
    // Walk up up to 5 parent levels to locate the container of the card
    for (let i = 0; i < 5; i++) {
      if (!cardContainer) break;
      // Search for any button or clickable element containing "+ Tag" or "Tag"
      tagButton = Array.from(cardContainer.querySelectorAll('button, div, span, a')).find(el => 
        el.textContent && (el.textContent.includes('+ Tag') || el.textContent.includes('Tag'))
      );
      if (tagButton) break;
      cardContainer = cardContainer.parentElement;
    }
    
    if (!tagButton) {
      console.log(`⚠️ Skip or already tagged: ${filename} (No '+ Tag' button found)`);
      continue;
    }
    
    console.log(`🏷️ Tagging ${filename} as '${tagToApply}'...`);
    
    // 3. Click the tag button to open the input field
    tagButton.click();
    
    // 4. Wait a split second (100ms) for React/Vue to render the input field
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // 5. Find the text input field in this card
    const input = cardContainer.querySelector('input[type="text"], input');
    if (input) {
      input.value = tagToApply;
      
      // Dispatch input and change events so React/Vue state registers the new text
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      
      // Simulate pressing Enter key to save
      input.dispatchEvent(new KeyboardEvent('keydown', {
        key: 'Enter',
        code: 'Enter',
        keyCode: 13,
        which: 13,
        bubbles: true
      }));
      
      // Blur the input (click away) as a solid fallback to trigger save
      input.blur();
      
      console.log(`✅ Successfully tagged ${filename} -> ${tagToApply}`);
      successCount++;
    } else {
      console.error(`❌ Failed to find the input field for ${filename} after clicking tag button.`);
    }
    
    // 6. Brief pause between cards to let React state cycles complete smoothly
    await new Promise(resolve => setTimeout(resolve, 150));
  }
  
  console.log(`\n🎉 COMPLETED! Successfully auto-tagged ${successCount} images.`);
}

// Execute the function
autoTagTurboFlow();
