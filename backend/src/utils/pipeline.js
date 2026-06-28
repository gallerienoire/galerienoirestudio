const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const db = require('./db');
const { v4: uuidv4 } = require('uuid');

const PIPELINE_DIR = '/home/team/shared/ai-pipeline';
const PYTHON_PATH = path.join(PIPELINE_DIR, 'venv/bin/python');
const ROOM_ANALYSIS_SCRIPT = path.join(PIPELINE_DIR, 'room_analysis.py');
const ARTWORK_GEN_SCRIPT = path.join(PIPELINE_DIR, 'artwork_generation.py');
const GUIDES_SCRIPT = path.join(PIPELINE_DIR, 'styling_shopping_guide.py');
const MOCKUP_SCRIPT = path.join(PIPELINE_DIR, 'mockup_generator.py');
const ARTWORK_OUTPUT_DIR = path.join(PIPELINE_DIR, 'generated-artwork');

/**
 * Spawn a Python script and capture its JSON output.
 * Returns a promise that resolves with the parsed JSON.
 */
function runPythonScript(scriptPath, args) {
  return new Promise((resolve, reject) => {
    const process = spawn(PYTHON_PATH, [scriptPath, ...args]);
    let stdout = '';
    let stderr = '';

    process.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    process.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    process.on('close', (code) => {
      if (code !== 0) {
        console.error(`Script ${scriptPath} failed with code ${code}`);
        console.error(`Stderr: ${stderr}`);
        return reject(new Error(`Script failed: ${stderr.substring(0, 500)}`));
      }
      try {
        const result = JSON.parse(stdout);
        resolve(result);
      } catch (err) {
        console.error(`Failed to parse JSON output from ${scriptPath}:`, err);
        console.error(`stdout preview: ${stdout.substring(0, 300)}`);
        reject(err);
      }
    });
  });
}

/**
 * Run the full AI pipeline for a project:
 * Step 1: Room Analysis → room_profile.json deliverable
 * Step 2: Artwork Generation → artwork_collection + individual artwork deliverables
 */
async function runFullPipeline(projectId, imagePath) {
  try {
    // Ensure artwork output directory exists
    fs.mkdirSync(ARTWORK_OUTPUT_DIR, { recursive: true });

    const absoluteImagePath = imagePath.startsWith('/')
      ? imagePath
      : path.join(__dirname, '../../', imagePath);

    // ── Step 1: Room Analysis ──────────────────────────────────────────────
    console.log(`[Pipeline] Step 1: Running room analysis for project ${projectId}`);
    const roomProfile = await runPythonScript(ROOM_ANALYSIS_SCRIPT, [
      absoluteImagePath, '--json'
    ]);

    // Store room_profile as deliverable
    const roomDeliverableId = uuidv4();
    await db.query(
      'INSERT INTO deliverables (id, project_id, type, content) VALUES (?, ?, ?, ?)',
      [roomDeliverableId, projectId, 'room_profile', JSON.stringify(roomProfile.room_profile)]
    );
    console.log(`[Pipeline] ✓ Room profile stored as deliverable ${roomDeliverableId}`);

    // Update project status
    await db.query(
      'UPDATE projects SET status = ? WHERE id = ?',
      ['analyzed', projectId]
    );

    // ── Step 2: Artwork Generation ─────────────────────────────────────────
    // Save room profile JSON to a temp file for Step 2 to read
    const tempProfilePath = path.join(os.tmpdir(), `gn-room-profile-${projectId}.json`);
    fs.writeFileSync(tempProfilePath, JSON.stringify(roomProfile));

    console.log(`[Pipeline] Step 2: Generating artworks for project ${projectId}`);

    // Create project-specific output dir within shared generated dir
    const projectOutputDir = path.join(ARTWORK_OUTPUT_DIR, projectId);
    fs.mkdirSync(projectOutputDir, { recursive: true });

    const artworkCollection = await runPythonScript(ARTWORK_GEN_SCRIPT, [
      tempProfilePath, '--output-dir', projectOutputDir, '--json'
    ]);

    // ── Step 3: Generate Artwork Images ────────────────────────────────────
    console.log(`[Pipeline] Step 3: Generating artwork images for project ${projectId}`);
    const IMAGE_GEN_SCRIPT = path.join(PIPELINE_DIR, 'generate_artwork_images.py');
    try {
      await runPythonScript(IMAGE_GEN_SCRIPT, [
        projectId, projectOutputDir
      ]);
      console.log(`[Pipeline] ✓ 5 artwork images generated`);
    } catch (imgErr) {
      // Image generation is non-critical; log warning and continue
      console.warn(`[Pipeline] ⚠️ Image generation warning: ${imgErr.message}`);
    }

    // Store full artwork collection as a deliverable
    const collectionDeliverableId = uuidv4();
    await db.query(
      'INSERT INTO deliverables (id, project_id, type, content, file_url) VALUES (?, ?, ?, ?, ?)',
      [
        collectionDeliverableId,
        projectId,
        'artwork_collection',
        JSON.stringify(artworkCollection),
        `/artwork/${projectId}/artwork_collection.json`
      ]
    );
    console.log(`[Pipeline] ✓ Artwork collection stored as deliverable ${collectionDeliverableId}`);

    // Store each individual artwork as a separate deliverable
    const pieces = artworkCollection.pieces || [];
    for (let i = 0; i < pieces.length; i++) {
      const piece = pieces[i];
      const artworkDeliverableId = uuidv4();
      const imageFileName = piece.generated_image || `artwork-${i + 1}.png`;
      const deliverableContent = {
        title: piece.title,
        slug: piece.slug,
        mood: piece.mood,
        description: piece.description,
        artwork_rationale: piece.artwork_rationale,
        color_rationale: piece.color_rationale,
        recommended_frame: piece.recommended_frame,
        recommended_lighting: piece.recommended_lighting,
        recommended_placement: piece.recommended_placement,
        dimensions_cm: piece.dimensions_cm,
        sort_order: i + 1
      };

      await db.query(
        'INSERT INTO deliverables (id, project_id, type, content, file_url) VALUES (?, ?, ?, ?, ?)',
        [
          artworkDeliverableId,
          projectId,
          'artwork',
          JSON.stringify(deliverableContent),
          `/artwork/${projectId}/${imageFileName}`
        ]
      );
      console.log(`[Pipeline]   [${i + 1}/5] ✓ Artwork "${piece.title}" stored`);
    }

    // Update project status to artwork_generated
    await db.query(
      'UPDATE projects SET status = ? WHERE id = ?',
      ['artwork_generated', projectId]
    );

    // ── Step 4: Styling & Shopping Guides ──────────────────────────────────
    console.log(`[Pipeline] Step 4: Generating styling & shopping guides for project ${projectId}`);
    try {
      const guidesResult = await runPythonScript(GUIDES_SCRIPT, [
        tempProfilePath, '--json'
      ]);

      // Extract styling guide
      const stylingGuide = guidesResult.styling_guide;
      if (stylingGuide) {
        const stylingDeliverableId = uuidv4();
        await db.query(
          'INSERT INTO deliverables (id, project_id, type, content, file_url) VALUES (?, ?, ?, ?, ?)',
          [
            stylingDeliverableId,
            projectId,
            'styling_guide',
            JSON.stringify(stylingGuide),
            `/artwork/${projectId}/styling-guide.json`
          ]
        );
        console.log(`[Pipeline] ✓ Styling guide stored as deliverable ${stylingDeliverableId}`);
      }

      // Extract shopping guide
      const shoppingGuide = guidesResult.shopping_guide;
      if (shoppingGuide) {
        const shoppingDeliverableId = uuidv4();
        await db.query(
          'INSERT INTO deliverables (id, project_id, type, content, file_url) VALUES (?, ?, ?, ?, ?)',
          [
            shoppingDeliverableId,
            projectId,
            'shopping_guide',
            JSON.stringify(shoppingGuide),
            `/artwork/${projectId}/shopping-guide.json`
          ]
        );
        console.log(`[Pipeline] ✓ Shopping guide stored as deliverable ${shoppingDeliverableId}`);
      }
    } catch (guideErr) {
      console.warn(`[Pipeline] ⚠️ Guides generation warning: ${guideErr.message}`);
    }

    // ── Step 5: Generate Room Mockup (artwork overlaid on actual photo) ────
    if (fs.existsSync(absoluteImagePath)) {
      console.log(`[Pipeline] Step 5: Generating room mockup for project ${projectId}`);
      try {
        await runPythonScript(MOCKUP_SCRIPT, [
          absoluteImagePath,
          tempProfilePath,
          projectOutputDir,
          '--output', path.join(projectOutputDir, 'mockup.jpg')
        ]);
        console.log(`[Pipeline] ✓ Mockup generated from actual room photo`);
      } catch (mockupErr) {
        console.warn(`[Pipeline] ⚠️ Mockup generation warning: ${mockupErr.message}`);
      }
    }

    // Clean up temp file
    try { fs.unlinkSync(tempProfilePath); } catch (e) { /* ignore */ }

    // Update project status to guides_generated
    await db.query(
      'UPDATE projects SET status = ? WHERE id = ?',
      ['guides_generated', projectId]
    );

    console.log(`[Pipeline] ✓ Full pipeline complete for project ${projectId}`);
    return { roomProfile, artworkCollection };

  } catch (err) {
    console.error(`[Pipeline] ✗ Pipeline failed for project ${projectId}:`, err);

    // Update status to failed
    try {
      await db.query(
        'UPDATE projects SET status = ? WHERE id = ?',
        ['failed', projectId]
      );
    } catch (dbErr) {
      console.error('[Pipeline] Failed to update project status:', dbErr);
    }

    throw err;
  }
}

/**
 * Legacy wrapper — runs Step 1 only (for backward compatibility with the
 * projects.js route, which calls runRoomAnalysis).
 */
async function runRoomAnalysis(projectId, imagePaths) {
  try {
    const imagePath = Array.isArray(imagePaths) ? imagePaths[0] : imagePaths;
    const result = await runFullPipeline(projectId, imagePath);
    return result.roomProfile;
  } catch (err) {
    // If full pipeline fails, fall back to Step 1 only
    console.log('[Pipeline] runRoomAnalysis wrapper caught error, returning null');
    throw err;
  }
}

module.exports = { runRoomAnalysis, runFullPipeline };
