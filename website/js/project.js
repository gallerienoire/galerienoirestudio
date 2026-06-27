/* Galerie Noire — Project Results Page v3
   Narrative analysis + preview + What Happens Next */

document.addEventListener('DOMContentLoaded', function() {
  var params = new URLSearchParams(window.location.search);
  var projectId = params.get('id');

  if (!projectId) {
    document.getElementById('project-content').innerHTML = '<div class="container" style="text-align:center;padding:4rem 0;"><p style="color:var(--warm-grey);">No project ID provided. <a href="/upload.html">Start a new project</a>.</p></div>';
    return;
  }

  fetchProject(projectId);
});

function fetchProject(id) {
  var contentEl = document.getElementById('project-content');
  contentEl.innerHTML = '<div class="container" style="text-align:center;padding:4rem 0;"><p style="color:var(--warm-grey);">Loading your project...</p></div>';

  fetch('/api/projects/' + encodeURIComponent(id))
    .then(function(response) {
      if (!response.ok) throw new Error('Project not found');
      return response.json();
    })
    .then(function(project) {
      renderProject(project);
    })
    .catch(function(err) {
      contentEl.innerHTML = '<div class="container" style="text-align:center;padding:4rem 0;"><p style="color:var(--warm-grey);">Could not load project. <a href="/upload.html">Start a new project</a>.</p></div>';
    });
}

function renderProject(project) {
  // Build deliverables lookup
  var deliverables = {};
  if (project.deliverables) {
    project.deliverables.forEach(function(d) {
      deliverables[d.type] = d.content;
    });
  }

  var roomProfile = deliverables.room_profile || null;
  var artworkData = deliverables.artwork_collection || null;
  var stylingSummary = deliverables.styling_summary || null;
  var pieces = artworkData && artworkData.pieces ? artworkData.pieces : (artworkData && artworkData.artworks ? artworkData.artworks : null);

  var html = '';

  // === Helpers ===
  function cap(s) {
    return s ? s.replace(/_/g, ' ').replace(/\b\w/g, function(l) { return l.toUpperCase(); }) : '';
  }
  function pct(n) { return Math.round((n || 0) * 100) + '%'; }

  // === Photo URL fix (may be JSON array string) ===
  var photoUrl = project.room_photo_url;
  if (typeof photoUrl === 'string' && photoUrl.charAt(0) === '[') {
    try { var parsed = JSON.parse(photoUrl); photoUrl = parsed[0] || null; } catch(e) { photoUrl = null; }
  }

  // === Hero Section ===
  var statusLabels = { uploaded: 'Uploaded', analyzing: 'Being Analyzed', analyzed: 'Analysis Complete', ready: 'Ready for Review', delivered: 'Delivered' };
  var statusLabel = statusLabels[project.status] || project.status;
  var tierNames = { starter: 'Starter Collection', signature: 'Signature Collection', estate: 'Estate Collection' };

  html += '<section class="upload-hero" style="padding-bottom:2rem;background:var(--soft-black);">';
  html += '<div class="container" style="text-align:center;">';
  html += '<div class="hero-decoration" style="margin:0 auto 2rem;"></div>';
  html += '<p class="section-label" style="color:var(--brass-gold);">Project ' + (project.id ? project.id.substring(0, 8) : '') + '</p>';
  html += '<h1>Your Room Transformation</h1>';
  html += '<div style="margin:1rem auto; display:inline-block; padding:0.5rem 1.5rem; border:1px solid var(--brass-gold); color:var(--brass-gold); font-size:0.8rem; text-transform:uppercase; letter-spacing:0.1em;">' + statusLabel + '</div>';
  html += '<p style="color:var(--warm-grey); margin-top:1rem;">' + (tierNames[project.tier] || project.tier) + '</p>';
  html += '</div></section>';

  // === Narrative Assessment (if room profile exists) ===
  if (roomProfile) {
    var archStyle = nested(roomProfile, 'architecture_style.primary_style') || 'Contemporary Modern';
    var roomType = nested(roomProfile, 'architecture.room_type_guess') || 'living room';
    var ceilingM = nested(roomProfile, 'architecture.ceiling_height_estimate_m') || '';
    var lightMood = nested(roomProfile, 'lighting.mood') || 'warm ambient';
    var colorTemp = nested(roomProfile, 'color_palette.color_temperature') || 'neutral';
    var colors = nested(roomProfile, 'color_palette.dominant_colors') || [];
    var artW = nested(roomProfile, 'wall_space.recommended_artwork_width_cm') || '';
    var artH = nested(roomProfile, 'wall_space.recommended_artwork_height_cm') || '';
    var viewDist = nested(roomProfile, 'wall_space.viewing_distance_m') || '';

    var roomTypeLabel = cap(roomType);
    var moodLabel = cap(lightMood);

    // --- 1. Our Assessment ---
    html += '<section class="section"><div class="container" style="max-width:800px;">';
    html += '<div class="section-header" style="text-align:left;margin:0 0 2rem;"><p class="section-label">Design Assessment</p><h2>Our Analysis</h2></div>';
    if (photoUrl) {
      html += '<img src="' + photoUrl + '" alt="Your room" style="width:100%;height:auto;border:1px solid rgba(197,165,90,0.1);margin-bottom:2rem;">';
    }
    html += '<div style="font-size:1.05rem;line-height:1.8;color:var(--warm-grey);">';
    html += '<p style="margin-bottom:1.5rem;">Your space reads as a <strong style="color:var(--cream);">' + archStyle + '</strong> interior with <strong style="color:var(--cream);">' + colorTemp + '</strong> tonalities.';
    if (ceilingM) html += ' The <strong style="color:var(--cream);">' + ceilingM + 'm</strong> ceiling height gives us generous vertical space to work with.';
    html += ' The lighting reads as <strong style="color:var(--cream);">' + moodLabel + '</strong> &mdash; ' + lightMoodDesc(lightMood) + '</p>';
    html += '<p>The existing palette of ' + paletteDesc(colors) + ' suggests artwork with depth &mdash; think charcoal abstracts with warm gold undertones, or a statement piece that anchors the room\'s natural flow.</p>';
    if (artW && artH) {
      html += '<p>The primary wall offers <strong style="color:var(--cream);">' + artW + 'cm x ' + artH + 'cm</strong> of prime display space';
      if (viewDist) html += ' with an optimal viewing distance of <strong style="color:var(--cream);">' + viewDist + 'm</strong>';
      html += ' &mdash; ideal for a large statement piece that commands attention without overwhelming the room.</p>';
    }
    html += '</div></div></section>';

    // --- 2. The Palette (curator's note + swatches) ---
    if (colors.length > 0) {
      html += '<section class="section section-dark"><div class="container" style="max-width:800px;">';
      html += '<div class="section-header" style="text-align:left;margin:0 0 2rem;"><p class="section-label">Color Direction</p><h2>The Palette</h2></div>';
      html += '<p style="color:var(--warm-grey);font-size:1.05rem;line-height:1.8;margin-bottom:2rem;">We\'ve identified <strong style="color:var(--cream);">' + colors.length + ' tonal families</strong> in your space. The ' + paletteNote(colors) + '</p>';
      html += '<div style="display:flex;gap:1.5rem;justify-content:center;flex-wrap:wrap;">';
      colors.forEach(function(c) {
        html += '<div style="text-align:center;"><div style="width:90px;height:90px;background:' + c.hex + ';border:1px solid rgba(197,165,90,0.15);margin-bottom:0.5rem;box-shadow:0 4px 12px rgba(0,0,0,0.3);"></div><div style="font-size:0.7rem;color:var(--warm-grey);letter-spacing:0.05em;">' + c.hex + '</div><div style="font-size:0.8rem;color:var(--cream);">' + pct(c.proportion) + '</div></div>';
      });
      html += '</div></div></section>';
    }

    // --- 3. The Opportunity ---
    html += '<section class="section"><div class="container" style="max-width:800px;">';
    html += '<div class="section-header" style="text-align:left;margin:0 0 2rem;"><p class="section-label">Design Direction</p><h2>The Opportunity</h2></div>';
    html += '<div style="font-size:1.05rem;line-height:1.8;color:var(--warm-grey);">';
    html += '<p style="margin-bottom:1.5rem;">';
    if (artW && artH) {
      html += 'The primary wall offers <strong style="color:var(--cream);">' + artW + 'cm x ' + artH + 'cm</strong> of display space';
      if (viewDist) html += ' with a viewing distance of <strong style="color:var(--cream);">' + viewDist + 'm</strong>';
      html += '. We recommend a single large-scale statement piece that anchors the room, or a curated diptych that plays with the room\'s symmetry.';
    } else {
      html += 'Based on our analysis, we\'ve identified the ideal wall space for your custom artwork. The architecture and lighting create a natural focal point that will be enhanced by the right piece.';
    }
    html += ' The <strong style="color:var(--cream);">' + moodLabel + '</strong> lighting allows us to play with both matte and metallic finishes &mdash; we\'ll recommend framing that complements the existing brass accents while adding a new layer of texture.</p>';
    html += '</div></div></section>';
  }

  // === Preview Section (show even if no artwork yet) ===
  html += '<section class="section section-dark"><div class="container" style="max-width:800px;text-align:center;">';
  html += '<div class="section-header fade-in"><p class="section-label">Visualization</p><h2>See Your Room Transformed</h2></div>';
  html += '<div style="margin-bottom:2rem;border:1px solid rgba(197,165,90,0.1);overflow:hidden;">';
  html += '<img src="/design/room-preview.jpg" alt="Your room transformed with custom artwork" style="width:100%;height:auto;display:block;">';
  html += '</div>';
  html += '<p style="color:var(--warm-grey);max-width:600px;margin:0 auto 1rem;font-size:1.05rem;line-height:1.7;">A preview of how your space could look with a custom-curated artwork as the centerpiece. This visualization adapts to your room\'s architecture, lighting, and palette.</p>';
  html += '</div></section>';

  // === What Happens Next (when artwork not yet ready) ===
  if (!pieces) {
    html += '<section class="section" style="background:var(--soft-black);"><div class="container">';
    html += '<div class="section-header fade-in"><p class="section-label">Coming Soon</p><h2>What Happens Next</h2></div>';
    html += '<div class="steps">';
    html += '<div class="step fade-in"><div class="step-number">01</div><h4>Artwork Curation</h4><p>Our AI analyzes your room profile &mdash; architecture, lighting, color palette &mdash; and commissions five original artworks tailored to your specific space.</p><div class="step-connector"></div></div>';
    html += '<div class="step fade-in"><div class="step-number">02</div><h4>Design Recommendations</h4><p>Once complete, you\'ll receive detailed styling guidance: optimal placement, framing suggestions, and layout adjustments that make the art feel native to your room.</p><div class="step-connector"></div></div>';
    html += '<div class="step fade-in"><div class="step-number">03</div><h4>Shopping Guide</h4><p>A curated list of furniture, lighting, and accessories &mdash; with exact product links &mdash; to complete your room transformation.</p><div class="step-connector"></div></div>';
    html += '<div class="step fade-in"><div class="step-number">04</div><h4>Before &amp; After</h4><p>A photorealistic visualization showing your room across day, night, and seasons &mdash; so you see the transformation before you make a single change.</p></div>';
    html += '</div></div></section>';
  }

  // === Artwork Collection ===
  if (pieces) {
    html += '<section class="section section-dark"><div class="container">';
    html += '<div class="section-header fade-in"><p class="section-label">Your Collection</p><h2>Curated Artworks</h2><p>Five original pieces created for your space.</p></div>';
    html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:2rem;">';

    pieces.forEach(function(art, i) {
      var artNum = (i + 1).toString().padStart(2, '0');
      var imgUrl = '';
      if (art.generated_image && art.generated_image.indexOf('/') === -1) {
        imgUrl = '/artwork/' + project.id + '/' + art.generated_image;
      } else if (art.imageUrl) {
        imgUrl = art.imageUrl;
      }
      var title = art.title || 'Untitled ' + artNum;
      var desc = art.description || '';
      var frameMat = art.recommended_frame ? (art.recommended_frame.material || art.recommended_frame.style || '') : (art.frameRecommendation || '');
      var placement = art.recommended_placement || art.placement || '';
      var frameDesc = art.recommended_frame ? art.recommended_frame.description : '';

      html += '<div class="fade-in" style="background:var(--soft-black);border:1px solid rgba(197,165,90,0.08);">';
      html += '<div style="aspect-ratio:4/3;background:var(--charcoal);overflow:hidden;">';
      if (imgUrl) {
        html += '<img src="' + imgUrl + '" alt="' + title + '" style="width:100%;height:100%;object-fit:cover;">';
      } else {
        html += '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:var(--warm-grey);font-size:0.8rem;">Artwork ' + artNum + '</div>';
      }
      html += '</div>';
      html += '<div style="padding:1.5rem;">';
      html += '<div style="font-family:var(--font-heading);font-size:1.1rem;margin-bottom:0.5rem;color:var(--cream);">' + title + '</div>';
      if (desc) html += '<p style="color:var(--warm-grey);font-size:0.85rem;line-height:1.6;margin-bottom:1rem;">' + desc + '</p>';
      if (frameMat || placement || frameDesc) {
        html += '<div style="border-top:1px solid rgba(197,165,90,0.08);padding-top:0.75rem;">';
        if (frameMat) html += '<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.25rem;"><span style="font-size:0.75rem;color:var(--brass-gold);text-transform:uppercase;letter-spacing:0.05em;">Frame: ' + frameMat + '</span></div>';
        if (frameDesc) html += '<p style="font-size:0.8rem;color:var(--warm-grey-light);margin-bottom:0.25rem;">' + frameDesc + '</p>';
        if (placement) html += '<p style="font-size:0.75rem;color:var(--warm-grey);font-style:italic;">Placement: ' + placement + '</p>';
        html += '</div>';
      }
      html += '</div></div>';
    });

    html += '</div></div></section>';
  }

  // === Styling Summary ===
  if (stylingSummary) {
    html += '<section class="section"><div class="container"><div class="section-header fade-in"><p class="section-label">Styling Guide</p><h2>Room Recommendations</h2></div>';
    html += '<div style="max-width:700px;margin:0 auto;">';

    var layoutChanges = stylingSummary.layout_changes || stylingSummary.layoutChanges || [];
    if (layoutChanges.length > 0) {
      html += '<div style="margin-bottom:2rem;"><h4 style="font-size:1.1rem;margin-bottom:1rem;">Layout Adjustments</h4>';
      if (Array.isArray(layoutChanges)) {
        layoutChanges.forEach(function(change) {
          html += '<div style="padding:0.75rem 0;border-bottom:1px solid rgba(197,165,90,0.06);display:flex;gap:0.75rem;align-items:flex-start;">';
          html += '<span style="color:var(--brass-gold);">&mdash;</span>';
          html += '<span style="color:var(--cream);font-size:0.9rem;">' + (typeof change === 'string' ? change : (change.description || change)) + '</span></div>';
        });
      }
      html += '</div>';
    }

    var viewDist = stylingSummary.viewing_distance || stylingSummary.viewingDistance || '';
    if (viewDist) {
      html += '<div style="margin-bottom:2rem;"><h4 style="font-size:1.1rem;margin-bottom:0.5rem;">Viewing Distance</h4>';
      html += '<p style="color:var(--warm-grey);font-size:0.9rem;">' + viewDist + '</p></div>';
    }
    html += '</div></div></section>';
  }

  // === Contact CTA ===
  html += '<section class="section section-dark" style="text-align:center;"><div class="container">';
  html += '<h2 class="fade-in">Questions about your project?</h2>';
  html += '<p style="color:var(--warm-grey);max-width:500px;margin:1rem auto 2rem;" class="fade-in">We\'re here to help refine your design.</p>';
  html += '<a href="/contact.html" class="btn btn-outline">Contact Us</a>';
  html += '</div></section>';

  document.getElementById('project-content').innerHTML = html;
}

/* ---- Helper functions ---- */

function nested(obj, path) {
  if (!obj) return null;
  var parts = path.split('.');
  var current = obj;
  for (var i = 0; i < parts.length; i++) {
    if (current === null || current === undefined || typeof current !== 'object') return null;
    current = current[parts[i]];
    if (current === undefined) return null;
  }
  return current;
}

function lightMoodDesc(mood) {
  var map = {
    'bright_crisp': 'bright and crisp &mdash; ideal for bold, high-contrast artwork.',
    'warm_ambient': 'warm and ambient &mdash; perfect for pieces with depth and texture.',
    'soft_diffuse': 'soft and diffuse &mdash; suits serene, tonal compositions.',
    'dramatic_directional': 'dramatic and directional &mdash; calls for artwork with strong contrast.',
    'mixed': 'mixed &mdash; versatile enough to support a range of artistic styles.'
  };
  return map[mood] || 'inviting and atmospheric &mdash; provides a beautiful backdrop for layered compositions.';
}

function paletteDesc(colors) {
  if (!colors || colors.length === 0) return 'warm neutrals and brass accents';
  var top = colors.slice(0, 3);
  var descs = [];
  top.forEach(function(c) {
    var name = colorName(c.hex);
    descs.push(name);
  });
  if (descs.length === 0) return 'warm neutrals';
  if (descs.length === 1) return descs[0];
  return descs.slice(0, -1).join(', ') + ', and ' + descs[descs.length - 1];
}

function paletteNote(colors) {
  if (!colors || colors.length === 0) return 'palette centers on warm beige and brass accents, giving us a luxe foundation to build from.';
  var top = colors[0];
  var name = colorName(top.hex);
  var p = Math.round((top.proportion || 0) * 100);
  return 'dominant <strong style="color:var(--cream);">' + name + '</strong> (' + top.hex + ') at <strong style="color:var(--cream);">' + p + '%</strong> provides an anchor, while the remaining ' + (colors.length - 1) + ' accents give us a refined foundation to build from.';
}

function colorName(hex) {
  var map = {
    '#ded2bf': 'warm beige',
    '#c5a55a': 'brass gold',
    '#1a1a1a': 'charcoal',
    '#f5f0eb': 'cream',
    '#1e3a2f': 'forest green',
    '#0d0d0d': 'soft black',
    '#8a8078': 'warm grey',
    '#2a2a2a': 'dark charcoal',
    '#ffffff': 'white',
    '#d4b86a': 'warm gold',
    '#e8dcc8': 'warm ivory',
    '#b8a88a': 'taupe',
    '#5a4a3a': 'espresso',
    '#3a4a3a': 'sage',
    '#4a5a6a': 'slate blue',
    '#6a5a4a': 'warm brown'
  };
  var lower = hex.toLowerCase();
  if (map[lower]) return map[lower];
  return hex;
}