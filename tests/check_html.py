with open('gallery.html', 'r', encoding='utf-8') as f:
    content = f.read()

for elem_id in ['rugNavList', 'galleryGrid', 'stat-rug-count', 'stat-total-imgs', 'stat-showing-count', 'activeRugTitle', 'activeRugSummary', 'searchInput', 'resTabs', 'lightboxModal']:
    count = content.count(f'id="{elem_id}"')
    print(f'Element id="{elem_id}" count: {count}')
