'use client'

import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { authApi } from '@/lib/auth-api'
import { useAuthStore } from '@/lib/auth-store'
import { validateEmail, validatePassword, validateName, getPasswordStrength } from '@/lib/validation'
import { Loader2 } from 'lucide-react'

export default function RegisterPage() {
  const router = useRouter()
  const { toast } = useToast()
  const setAuth = useAuthStore((state) => state.setAuth)
  
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [acceptedTerms, setAcceptedTerms] = useState(false)
  
  const [nameError, setNameError] = useState<string | null>(null)
  const [emailError, setEmailError] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [termsError, setTermsError] = useState<string | null>(null)
  
  const [isLoading, setIsLoading] = useState(false)
  const [generalError, setGeneralError] = useState<string | null>(null)

  const passwordStrength = password ? getPasswordStrength(password) : null

  const handleNameChange = (value: string) => {
    setName(value)
    if (nameError) {
      const error = validateName(value)
      setNameError(error)
    }
  }

  const handleNameBlur = () => {
    const error = validateName(name)
    setNameError(error)
  }

  const handleEmailChange = (value: string) => {
    setEmail(value)
    if (emailError) {
      const error = validateEmail(value)
      setEmailError(error)
    }
  }

  const handleEmailBlur = () => {
    const error = validateEmail(email)
    setEmailError(error)
  }

  const handlePasswordChange = (value: string) => {
    setPassword(value)
    if (passwordError) {
      const error = validatePassword(value)
      setPasswordError(error)
    }
  }

  const handlePasswordBlur = () => {
    const error = validatePassword(password)
    setPasswordError(error)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setGeneralError(null)

    // Validate all fields
    const nameValidation = validateName(name)
    const emailValidation = validateEmail(email)
    const passwordValidation = validatePassword(password)
    
    setNameError(nameValidation)
    setEmailError(emailValidation)
    setPasswordError(passwordValidation)

    if (!acceptedTerms) {
      setTermsError('You must accept the terms of service')
      return
    } else {
      setTermsError(null)
    }

    if (nameValidation || emailValidation || passwordValidation) {
      return
    }

    setIsLoading(true)

    try {
      const response = await authApi.register({ name, email, password })
      setAuth(response.token, response.user)
      
      toast({
        title: 'Success',
        description: 'Your account has been created successfully',
      })

      router.push('/dashboard')
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Registration failed. Please try again.'
      setGeneralError(errorMessage)
      
      toast({
        variant: 'destructive',
        title: 'Registration failed',
        description: errorMessage,
      })
    } finally {
      setIsLoading(false)
    }
  }

  const getStrengthColor = (strength: 'weak' | 'medium' | 'strong') => {
    switch (strength) {
      case 'weak':
        return 'bg-red-500'
      case 'medium':
        return 'bg-yellow-500'
      case 'strong':
        return 'bg-green-500'
    }
  }

  const getStrengthWidth = (score: number) => {
    return `${(score / 6) * 100}%`
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4 py-8">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">Create an account</CardTitle>
          <CardDescription className="text-center">
            Enter your information to get started
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {generalError && (
              <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-md">
                {generalError}
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                value={name}
                onChange={(e) => handleNameChange(e.target.value)}
                onBlur={handleNameBlur}
                disabled={isLoading}
                className={nameError ? 'border-red-500' : ''}
              />
              {nameError && (
                <p className="text-sm text-red-600 dark:text-red-400">{nameError}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => handleEmailChange(e.target.value)}
                onBlur={handleEmailBlur}
                disabled={isLoading}
                className={emailError ? 'border-red-500' : ''}
              />
              {emailError && (
                <p className="text-sm text-red-600 dark:text-red-400">{emailError}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => handlePasswordChange(e.target.value)}
                onBlur={handlePasswordBlur}
                disabled={isLoading}
                className={passwordError ? 'border-red-500' : ''}
              />
              {passwordError && (
                <p className="text-sm text-red-600 dark:text-red-400">{passwordError}</p>
              )}
              
              {/* Password strength indicator */}
              {password && passwordStrength && (
                <div className="space-y-1">
                  <div className="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${getStrengthColor(passwordStrength.strength)}`}
                      style={{ width: getStrengthWidth(passwordStrength.score) }}
                    />
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Password strength: <span className="font-medium capitalize">{passwordStrength.strength}</span>
                  </p>
                </div>
              )}
              
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Must be at least 8 characters with uppercase and digit
              </p>
            </div>

            <div className="flex items-start space-x-2">
              <Checkbox
                id="terms"
                checked={acceptedTerms}
                onCheckedChange={(checked) => {
                  setAcceptedTerms(checked as boolean)
                  if (checked) setTermsError(null)
                }}
                disabled={isLoading}
                className={termsError ? 'border-red-500' : ''}
              />
              <div className="grid gap-1.5 leading-none">
                <label
                  htmlFor="terms"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  I accept the terms of service
                </label>
                {termsError && (
                  <p className="text-sm text-red-600 dark:text-red-400">{termsError}</p>
                )}
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                'Create account'
              )}
            </Button>
            
            <p className="text-sm text-center text-gray-600 dark:text-gray-400">
              Already have an account?{' '}
              <Link
                href="/login"
                className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
              >
                Sign in
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
