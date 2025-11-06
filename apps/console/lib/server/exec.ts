import { spawn, ChildProcess } from 'child_process'
import path from 'path'

export interface ExecStreamOptions {
  cwd: string
  timeout?: number // in milliseconds
  env?: NodeJS.ProcessEnv
}

/**
 * Execute a command and return the child process for streaming output
 */
export function execStream(
  cmd: string,
  args: string[],
  options: ExecStreamOptions
): ChildProcess {
  const { cwd, timeout = 600000, env = process.env } = options

  // Security: validate working directory
  const allowedDirs = ['/home/doctor/temponest']
  const resolvedCwd = path.resolve(cwd)

  if (!allowedDirs.some((dir) => resolvedCwd.startsWith(dir))) {
    throw new Error(`Working directory not allowed: ${cwd}`)
  }

  const child = spawn(cmd, args, {
    cwd: resolvedCwd,
    env,
    shell: false, // Security: disable shell to prevent injection
  })

  // Set timeout
  if (timeout > 0) {
    setTimeout(() => {
      if (!child.killed) {
        child.kill('SIGTERM')
        setTimeout(() => {
          if (!child.killed) {
            child.kill('SIGKILL')
          }
        }, 5000)
      }
    }, timeout)
  }

  return child
}

/**
 * Execute a command and collect all output
 */
export async function execCollect(
  cmd: string,
  args: string[],
  options: ExecStreamOptions
): Promise<{ stdout: string; stderr: string; exitCode: number | null }> {
  return new Promise((resolve, reject) => {
    const child = execStream(cmd, args, options)
    let stdout = ''
    let stderr = ''

    child.stdout?.on('data', (chunk) => {
      stdout += chunk.toString()
    })

    child.stderr?.on('data', (chunk) => {
      stderr += chunk.toString()
    })

    child.on('error', (error) => {
      reject(error)
    })

    child.on('close', (exitCode) => {
      resolve({ stdout, stderr, exitCode })
    })
  })
}

/**
 * Validate and sanitize shell arguments to prevent injection
 */
export function sanitizeArgs(args: string[]): string[] {
  return args.map((arg) => {
    // Remove potentially dangerous characters
    return arg.replace(/[;&|`$()]/g, '')
  })
}
