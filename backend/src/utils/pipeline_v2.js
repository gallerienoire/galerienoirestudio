const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const db = require('./db');
const { v4: uuidv4 } = require('uuid');

const PIPELINE_DIR = '/home/team/shared/ai-pipeline';
const PYTHON_PATH = path.join(PIPELINE_DIR, 'venv/bin/python');
const ORCHESTRATOR_SCRIPT = path.join(PIPELINE_DIR, 'pipeline_orchestrator.py');
const ARTWORK_GEN_SCRIPT = path.join(PIPELINE_DIR, 'artwork_generation.py');
const IMAGE_GEN_SCRIPT = path.join(PIPELINE_DIR, 'generate_artwork_images.py');
const MOCKUP_SCRIPT = path.join(PIPELINE_DIR, 'mockup_generator.py');
const GUIDES_SCRIPT = path.join(PIPELINE_DIR, 'styling_shopping_guide.py');
// Stage 8 Luxury Curator (to be added)
const LUXURY_CURATOR_SCRIPT = path.join(PIPELINE_DIR, 'luxury_curator.py');

const ARTWORK_OUTPUT_DIR = path.join(PIPELINE_DIR, 'generated-artwork');

/**
 * Spawn a Python script and capture its JSON output.
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
 * Run the new 8-Stage AI Pipeline
 */
async function runFullPipelineV2(projectId, imagePath) {
  const outputDir = path.join(PIPELINE_DIR, 'output', projectId);
  fs.mkdirSync(outputDir, { recursive: true });

  const absoluteImagePath = imagePath.startsWith('/')
    ? imagePath
    : path.join(__dirname, '../../', imagePath);

  try {
    // --- STAGES 1-5: Verification & Design ---
    console.log(`[Pipeline V2] Running Stages 1-5 (Orchestrator) for ${projectId}`);
    const stages1to5 = await runPythonScript(ORCHESTRATOR_SCRIPT, [
      absoluteImagePath, '--output-dir', outputDir
    ]);

    // Store intermediate deliverables for richer output
    const stage3Path = stages1to5.stage3_consensus;
    const stage4Path = stages1to5.stage4_design;
    const stage5Path = stages1to5.stage5_art_brief;

    const verifiedProfile = JSON.parse(fs.readFileSync(stage3Path, 'utf8')).verified_room_profile;
    const designAssessment = JSON.parse(fs.readFileSync(stage4Path, 'utf8')).design_assessment;
    const artBrief = JSON.parse(fs.readFileSync(stage5Path, 'utf8')).artwork_brief;

    await db.query(
      'INSERT INTO deliverables (id, project_id, type, content) VALUES (?, ?, ?, ?)',
      [uuidv4(), projectId, 'verified_profile', JSON.stringify(verifiedProfile)]
    );
    await db.query(
      'INSERT INTO deliverables (id, project_id, type, content) VALUES (?, ?, ?, ?)',
      [uuidv4(), projectId, 'design_recommendations', JSON.stringify(designAssessment)]
    );
    await db.query(
      'INSERT INTO deliverables (id, project_id, type, content) VALUES (?, ?, ?, ?)',
      [uuidv4(), projectId, 'artwork_brief', JSON.stringify(artBrief)]
    );

    // Update status to analyzed
    await db.query('UPDATE projects SET status = ? WHERE id = ?', ['analyzed', projectId]);

    // --- STAGE 6: Artwork Generation ---
    console.log(`[Pipeline V2] Stage 6: Generating artworks for ${projectId}`);
    const projectOutputDir = path.join(ARTWORK_OUTPUT_DIR, projectId);
    fs.mkdirSync(projectOutputDir, { recursive: true });

    // Note: legacy script expects the full stage5 JSON or similar
    const artworkCollection = await runPythonScript(ARTWORK_GEN_SCRIPT, [
      stage5Path, '--output-dir', projectOutputDir, '--json'
    ]);

    // Generate actual images
    try {
      await runPythonScript(IMAGE_GEN_SCRIPT, [projectId, projectOutputDir]);
    } catch (e) {
      console.warn(`[Pipeline V2] Image generation warning: ${e.message}`);
    }

    // Store artwork deliverables
    const pieces = artworkCollection.pieces || [];
    for (let i = 0; i < pieces.length; i++) {
      const piece = pieces[i];
      const imageFileName = piece.generated_image || `artwork-${i + 1}.png`;
      await db.query(
        'INSERT INTO deliverables (id, project_id, type, content, file_url) VALUES (?, ?, ?, ?, ?)',
        [
          uuidv4(),
          projectId,
          'artwork',
          JSON.stringify(piece),
          `/artwork/${projectId}/${imageFileName}`
        ]
      );
    }

    await db.query('UPDATE projects SET status = ? WHERE id = ?', ['artwork_generated', projectId]);

    // --- STAGE 7: Mockup Specialist ---
    console.log(`[Pipeline V2] Stage 7: Generating mockup for ${projectId}`);
    try {
      await runPythonScript(MOCKUP_SCRIPT, [
        absoluteImagePath,
        stage3Path, // Use verified profile for better mockup placement
        projectOutputDir,
        '--output', path.join(projectOutputDir, 'mockup.jpg')
      ]);
      
      await db.query(
        'INSERT INTO deliverables (id, project_id, type, content, file_url) VALUES (?, ?, ?, ?, ?)',
        [uuidv4(), projectId, 'room_mockup', JSON.stringify({ description: 'Artwork overlaid in your actual room' }), `/artwork/${projectId}/mockup.jpg`]
      );
    } catch (e) {
      console.warn(`[Pipeline V2] Mockup warning: ${e.message}`);
    }

    // --- LEGACY: Styling & Shopping Guides (Until Stage 8 is ready) ---
    console.log(`[Pipeline V2] Generating styling & shopping guides for ${projectId}`);
    try {
      const guidesResult = await runPythonScript(GUIDES_SCRIPT, [
        stage3Path, '--json'
      ]);
      if (guidesResult.styling_guide) {
        await db.query(
          'INSERT INTO deliverables (id, project_id, type, content, file_url) VALUES (?, ?, ?, ?, ?)',
          [uuidv4(), projectId, 'styling_guide', JSON.stringify(guidesResult.styling_guide), `/artwork/${projectId}/styling-guide.json`]
        );
      }
      if (guidesResult.shopping_guide) {
        await db.query(
          'INSERT INTO deliverables (id, project_id, type, content, file_url) VALUES (?, ?, ?, ?, ?)',
          [uuidv4(), projectId, 'shopping_guide', JSON.stringify(guidesResult.shopping_guide), `/artwork/${projectId}/shopping-guide.json`]
        );
      }
    } catch (e) {
      console.warn(`[Pipeline V2] Guides warning: ${e.message}`);
    }

    // --- STAGE 8: Luxury Curator ---
    console.log(`[Pipeline V2] Stage 8: Luxury Curator for ${projectId}`);
    try {
      const curationResult = await runPythonScript(LUXURY_CURATOR_SCRIPT, [
        '--project-id', projectId
      ]);
      
      await db.query(
        'INSERT INTO deliverables (id, project_id, type, content) VALUES (?, ?, ?, ?)',
        [uuidv4(), projectId, 'curated_deliverable', JSON.stringify(curationResult)]
      );
      console.log(`[Pipeline V2] ✓ Luxury curation complete`);
    } catch (e) {
      console.warn(`[Pipeline V2] Luxury Curator warning: ${e.message}`);
    }

    await db.query('UPDATE projects SET status = ? WHERE id = ?', ['completed', projectId]);
    console.log(`[Pipeline V2] ✓ Full 8-stage pipeline complete for ${projectId}`);

  } catch (err) {
    console.error(`[Pipeline V2] ✗ Failed for project ${projectId}:`, err);
    await db.query('UPDATE projects SET status = ? WHERE id = ?', ['failed', projectId]);
    throw err;
  }
}

module.exports = { runFullPipelineV2 };
