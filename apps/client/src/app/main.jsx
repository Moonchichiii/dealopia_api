import React from 'react'
import ReactDOM from 'react-dom/client'

import { MONOREPO_NAME } from '@dealopia/shared'

function App() {
  return <div>{MONOREPO_NAME} client is running.</div>
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
