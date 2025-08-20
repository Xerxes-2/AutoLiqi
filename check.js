// Using Node.js built-in fetch (Node 18+)

async function checkUpdates() {
  try {
    // Get current version from maj-soul
    const versionResponse = await fetch('https://game.maj-soul.com/1/version.json', {
      timeout: 10000
    });
    const versionData = await versionResponse.json();
    const version = versionData.version;

    // Get protobuf prefix
    const resVersionResponse = await fetch(`https://game.maj-soul.com/1/resversion${version}.json`, {
      timeout: 10000
    });
    const resVersionData = await resVersionResponse.json();
    const liqiPrefix = resVersionData.res['res/proto/liqi.json'].prefix;
    const lqbinPrefix = resVersionData.res['res/config/lqc.lqbin'].prefix;

    // Get latest GitHub release
    const githubResponse = await fetch('https://api.github.com/repos/Xerxes-2/AutoLiqi/releases/latest', {
      headers: {
        'Authorization': process.env.GITHUB_TOKEN ? `Bearer ${process.env.GITHUB_TOKEN}` : undefined,
        'X-GitHub-Api-Version': '2022-11-28'
      },
      timeout: 10000
    });

    if (githubResponse.headers.get('X-RateLimit-Remaining') === '0') {
      throw new Error('GitHub API rate limit exceeded');
    }

    const githubData = await githubResponse.json();
    const currentTag = githubData.tag_name;

    // Parse release description to get current lqbing version
    const description = githubData.body || '';
    const lqbinMatch = description.match(/lqc\.lqbin\s+(\S+)/);
    const currentLqbinVersion = lqbinMatch ? lqbinMatch[1] : '';

    // Check if updates are needed
    const liqiUpdateNeeded = currentTag !== liqiPrefix;
    const lqbinUpdateNeeded = currentLqbinVersion !== lqbinPrefix;
    const updateNeeded = liqiUpdateNeeded || lqbinUpdateNeeded;

    const result = {
      updateNeeded,
      liqiUpdateNeeded,
      lqbinUpdateNeeded,
      currentVersions: {
        version,
        liqiPrefix,
        lqbinPrefix,
        currentTag,
        currentLqbinVersion
      },
      timestamp: new Date().toISOString()
    };

    console.log('Update check result:', JSON.stringify(result, null, 2));

    // If update is needed, simulate webhook trigger
    if (updateNeeded) {
      console.log('Update needed! Would trigger GitHub Action...');
      if (process.env.GITHUB_TOKEN) {
        await triggerGitHubAction(result);
      } else {
        console.log('GITHUB_TOKEN not set, skipping webhook trigger');
      }
    } else {
      console.log('No updates needed');
    }

    return result;
  } catch (error) {
    console.error('Error checking updates:', error);
    throw error;
  }
}

async function triggerGitHubAction(updateInfo) {
  try {
    const webhookResponse = await fetch('https://api.github.com/repos/Xerxes-2/AutoLiqi/dispatches', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        event_type: 'update_available',
        client_payload: updateInfo
      })
    });

    if (!webhookResponse.ok) {
      throw new Error(`GitHub webhook failed: ${webhookResponse.status}`);
    }

    console.log('Successfully triggered GitHub Action');
  } catch (error) {
    console.error('Failed to trigger GitHub Action:', error);
    throw error;
  }
}

// Run the check
checkUpdates().catch(console.error);