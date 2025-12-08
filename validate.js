addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  if (request.method !== "POST") {
    return new Response("Method not allowed", {status: 405})
  }

  const {cookie} = await request.json()

  if (!cookie || cookie.length < 600) {
    return new Response(JSON.stringify({
      success: false,
      user: "Invalid",
      display: "Invalid",
      userid: 0,
      robux: 0,
      premium: "No"
    }), {headers: {"Content-Type": "application/json"}})
  }

  // REAL VALIDATION USING ROBLOX API
  try {
    const userRes = await fetch("https://users.roblox.com/v1/users/authenticated", {
      headers: {"Cookie": `.ROBLOSECURITY=${cookie}`}
    })
    if (!userRes.ok) throw new Error("Dead cookie")
    const user = await userRes.json()

    const robuxRes = await fetch(`https://economy.roblox.com/v1/users/${user.id}/currency`, {
      headers: {"Cookie": `.ROBLOSECURITY=${cookie}`}
    })
    const robuxData = await robuxRes.json()

    return new Response(JSON.stringify({
      success: true,
      user: user.name,
      display: user.displayName,
      userid: user.id,
      robux: robuxData.robux || 0,
      premium: "Yes",
      headshot: `https://www.roblox.com/headshot-thumbnail/image?userId=${user.id}&width=150&height=150&format=png`
    }), {headers: {"Content-Type": "application/json"}})
  } catch(e) {
    return new Response(JSON.stringify({
      success: false,
      user: "Dead",
      display: "Dead",
      userid: 0,
      robux: 0,
      premium: "No"
    }), {headers: {"Content-Type": "application/json"}})
  }
}
