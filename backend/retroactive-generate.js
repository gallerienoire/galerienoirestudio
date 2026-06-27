#!/usr/bin/env node
/**
 * Retroactive Artwork Generation
 * Generates artwork for projects that were analyzed before the pipeline
 * was upgraded to auto-run Step 2.
 * 
 * Usage: node retroactive-generate.js <project-id-1> [project-id-2] ...
 */

const path = require('path');
const fs = require('fs');
const os = require('os');
const { v4: uuidv4 } = require('uuid');

// Import the pipeline's helper functions
const pipelinePath = path.join(__dirname, 'src/utils/pipeline');
const { runFullPipeline } = require(pipelinePath);

// Import the db helper
const db = require('./src/utils/db');

const ARTWORK_OUTPUT_DIR = '/home/team/shared/ai-pipeline/generated-artwork';

async function generateArtworkForProject(projectId) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`Processing project: ${projectId}`);
  console.log(`${'='.repeat(60)}`);

  try {
    // 1. Get project info
    const projects = await db.query('SELECT id, status, room_photo_url FROM projects WHERE id = ?', [projectId]);

    if (projects.length === 0) {
      console.log(`  ✗ Project ${projectId} not found`);
      return false;
    }

    const project = projects[0];
    console.log(`  Status: ${project.status}`);
    console.log(`  Photo: ${project.room_photo_url}`);

    if (project.status === 'artwork_generated') {
      console.log(`  ✓ Already has artwork — skipping`);
      return true;
    }

    // 2. Get the room_profile deliverable
    const deliverables = await db.query(
      "SELECT id, content FROM deliverables WHERE project_id = ? AND type = 'room_profile' ORDER BY id DESC LIMIT 1",
      [projectId]
    );

    if (deliverables.length === 0) {
      console.log(`  ✗ No room_profile deliverable found — re-running full pipeline`);
      // Try to get the original photo
      const absoluteImagePath = project.room_photo_url
        ? path.join('/home/team/shared/backend', project.room_photo_url)
        : null;

      if (absoluteImagePath && fs.existsSync(absoluteImagePath)) {
        console.log(`  Photo exists at: ${absoluteImagePath}`);
        await runFullPipeline(projectId, absoluteImagePath);
        console.log(`  ✓ Full pipeline completed for ${projectId}`);
        return true;
      } else {
        console.log(`  ✗ No photo available for re-analysis`);
        return false;
      }
    }

    const deliverable = deliverables[0];

    // 3. Parse the room profile content
    // The content field is a JSON string containing the room_profile fields
    let roomProfileData;
    try {
      roomProfileData = JSON.parse(deliverable.content);
    } catch (e) {
      console.log(`  ✗ Failed to parse room profile JSON: ${e.message}`);
      return false;
    }

    // 4. Wrap in the expected format (Step 1 output format)
    const wrappedProfile = {
      room_profile: roomProfileData,
      metadata: {
        engine_version: '1.0.0',
        pipeline_step: 1,
        source_project: projectId
      }
    };

    // 5. Save to temp file
    const tempProfilePath = path.join(os.tmpdir(), `gn-retro-profile-${projectId}.json`);
    fs.writeFileSync(tempProfilePath, JSON.stringify(wrappedProfile, null, 2));
    console.log(`  ✓ Saved room profile to ${tempProfilePath}`);

    // 6. Run artwork generation
    const { spawn } = require('child_process');
    const pythonPath = '/home/team/shared/ai-pipeline/venv/bin/python';
    const scriptPath = '/home/team/shared/ai-pipeline/artwork_generation.py';
    const projectOutputDir = path.join(ARTWORK_OUTPUT_DIR, projectId);

    fs.mkdirSync(projectOutputDir, { recursive: true });

    console.log(`  Running artwork_generation.py...`);

    const result = await new Promise((resolve, reject) => {
      const process = spawn(pythonPath, [scriptPath, tempProfilePath, '--output-dir', projectOutputDir, '--json']);
      let stdout = '';
      let stderr = '';

      process.stdout.on('data', (data) => { stdout += data.toString(); });
      process.stderr.on('data', (data) => { stderr += data.toString(); });

      process.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Script failed with code ${code}: ${stderr.substring(0, 300)}`));
          return;
        }
        try {
          resolve(JSON.parse(stdout));
        } catch (e) {
          reject(new Error(`JSON parse error: ${e.message}. stdout: ${stdout.substring(0, 200)}`));
        }
      });
    });

    console.log(`  ✓ Artwork generated: ${result.count} pieces`);

    // 7. Store artwork_collection deliverable
    const collectionDeliverableId = uuidv4();
    await db.query(
      'INSERT INTO deliverables (id, project_id, type, content, file_url) VALUES (?, ?, ?, ?, ?)',
      [
        collectionDeliverableId,
        projectId,
        'artwork_collection',
        JSON.stringify(result),
        `/artwork/${projectId}/artwork_collection.json`
      ]
    );
    console.log(`  ✓ artwork_collection deliverable stored`);

    // 8. Store each individual artwork as a deliverable
    const pieces = result.pieces || [];
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
      console.log(`  [${i + 1}/5] ✓ "${piece.title}" stored`);
    }

    // 9. Update project status
    await db.query(
      'UPDATE projects SET status = ? WHERE id = ?',
      ['artwork_generated', projectId]
    );
    console.log(`  ✓ Status updated to artwork_generated`);

    // Clean up temp file
    try { fs.unlinkSync(tempProfilePath); } catch (e) { /* ignore */ }

    return true;

  } catch (err) {
    console.error(`  ✗ Failed: ${err.message}`);
    return false;
  }
}

// Main
async function main() {
  const projectIds = process.argv.slice(2);
  if (projectIds.length === 0) {
    console.log('Usage: node retroactive-generate.js <project-id-1> [project-id-2] ...');
    process.exit(1);
  }

  console.log('=== Retroactive Artwork Generation ===');
  console.log(`Projects to process: ${projectIds.length}`);

  let successCount = 0;
  for (const projectId of projectIds) {
    const ok = await generateArtworkForProject(projectId);
    if (ok) successCount++;
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log(`Results: ${successCount}/${projectIds.length} projects completed`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});