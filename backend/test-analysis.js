const { runRoomAnalysis } = require('./src/utils/pipeline');

async function test() {
  try {
    const projectId = '0799151d-b39f-437e-ada0-89816c282b48';
    const imagePath = '/home/agent-full-stack-developer/galerie-noire-backend/uploads/e5e10e20-19c3-48ec-af4f-c5c903fe4988.jpg';
    console.log('Starting analysis...');
    const result = await runRoomAnalysis(projectId, imagePath);
    console.log('Analysis result:', JSON.stringify(result, null, 2));
  } catch (err) {
    console.error('Test failed:', err);
  }
}

test();
