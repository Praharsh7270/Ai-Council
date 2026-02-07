'use client'

import { useState, FormEvent, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useToast } from '@/hooks/use-toast'
import { authApi } from '@/lib/auth-api'
import { useAuthStore } from '@/lib/auth-store'
import { validateEmail, validateName, validatePassword } from '@/lib/validation'
import { Loader2, User, Lock, Trash2 } from 'lucide-react'

export default function ProfilePage() {
  const router = useRouter()
  const { toast } = useToast()
  const { user, isAuthenticated, updateUser, logout } = useAuthStore()
  
  // Profile edit state
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [nameError, setNameError] = useState<string | null>(null)
  const [emailError, setEmailError] = useState<string | null>(null)
  const [isEditingProfile, setIsEditingProfile] = useState(false)
  
  // Password change state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordError, setNewPasswordError] = useState<string | null>(null)
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  
  // Delete account state
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [isDeletingAccount, setIsDeletingAccount] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    
    if (user) {
      setName(user.name)
      setEmail(user.email)
    }
  }, [isAuthenticated, user, router])

  const handleProfileSubmit = async (e: FormEvent) => {
    e.preventDefault()

    // Validate
    const nameValidation = validateName(name)
    const emailValidation = validateEmail(email)
    
    setNameError(nameValidation)
    setEmailError(emailValidation)

    if (nameValidation || emailValidation) {
      return
    }

    setIsEditingProfile(true)

    try {
      const updatedUser = await authApi.updateProfile({ name, email })
      updateUser(updatedUser)
      
      toast({
        title: 'Success',
        description: 'Your profile has been updated',
      })
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to update profile'
      
      toast({
        variant: 'destructive',
        title: 'Update failed',
        description: errorMessage,
      })
    } finally {
      setIsEditingProfile(false)
    }
  }

  const handlePasswordSubmit = async (e: FormEvent) => {
    e.preventDefault()

    // Validate
    if (!currentPassword) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Current password is required',
      })
      return
    }

    const passwordValidation = validatePassword(newPassword)
    setNewPasswordError(passwordValidation)

    if (passwordValidation) {
      return
    }

    setIsChangingPassword(true)

    try {
      await authApi.changePassword({ currentPassword, newPassword })
      
      toast({
        title: 'Success',
        description: 'Your password has been changed',
      })
      
      setCurrentPassword('')
      setNewPassword('')
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to change password'
      
      toast({
        variant: 'destructive',
        title: 'Password change failed',
        description: errorMessage,
      })
    } finally {
      setIsChangingPassword(false)
    }
  }

  const handleDeleteAccount = async () => {
    setIsDeletingAccount(true)

    try {
      await authApi.deleteAccount()
      
      toast({
        title: 'Account deleted',
        description: 'Your account has been permanently deleted',
      })
      
      await logout()
      router.push('/')
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to delete account'
      
      toast({
        variant: 'destructive',
        title: 'Deletion failed',
        description: errorMessage,
      })
    } finally {
      setIsDeletingAccount(false)
      setIsDeleteDialogOpen(false)
    }
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Profile Information */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <User className="h-5 w-5" />
              <CardTitle>Profile Information</CardTitle>
            </div>
            <CardDescription>
              Update your account details
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleProfileSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="profile-name">Name</Label>
                <Input
                  id="profile-name"
                  type="text"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value)
                    if (nameError) setNameError(null)
                  }}
                  disabled={isEditingProfile}
                  className={nameError ? 'border-red-500' : ''}
                />
                {nameError && (
                  <p className="text-sm text-red-600 dark:text-red-400">{nameError}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="profile-email">Email</Label>
                <Input
                  id="profile-email"
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value)
                    if (emailError) setEmailError(null)
                  }}
                  disabled={isEditingProfile}
                  className={emailError ? 'border-red-500' : ''}
                />
                {emailError && (
                  <p className="text-sm text-red-600 dark:text-red-400">{emailError}</p>
                )}
              </div>

              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={isEditingProfile}
                >
                  {isEditingProfile ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    'Save changes'
                  )}
                </Button>
              </div>
            </CardContent>
          </form>
        </Card>

        {/* Change Password */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Lock className="h-5 w-5" />
              <CardTitle>Change Password</CardTitle>
            </div>
            <CardDescription>
              Update your password to keep your account secure
            </CardDescription>
          </CardHeader>
          <form onSubmit={handlePasswordSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="current-password">Current Password</Label>
                <Input
                  id="current-password"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  disabled={isChangingPassword}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-password">New Password</Label>
                <Input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => {
                    setNewPassword(e.target.value)
                    if (newPasswordError) setNewPasswordError(null)
                  }}
                  disabled={isChangingPassword}
                  className={newPasswordError ? 'border-red-500' : ''}
                />
                {newPasswordError && (
                  <p className="text-sm text-red-600 dark:text-red-400">{newPasswordError}</p>
                )}
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Must be at least 8 characters with uppercase and digit
                </p>
              </div>

              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={isChangingPassword}
                >
                  {isChangingPassword ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Changing...
                    </>
                  ) : (
                    'Change password'
                  )}
                </Button>
              </div>
            </CardContent>
          </form>
        </Card>

        {/* Delete Account */}
        <Card className="border-red-200 dark:border-red-900">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Trash2 className="h-5 w-5 text-red-600 dark:text-red-400" />
              <CardTitle className="text-red-600 dark:text-red-400">Danger Zone</CardTitle>
            </div>
            <CardDescription>
              Permanently delete your account and all associated data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="destructive">
                  Delete Account
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Are you absolutely sure?</DialogTitle>
                  <DialogDescription>
                    This action cannot be undone. This will permanently delete your account
                    and remove all your data from our servers.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setIsDeleteDialogOpen(false)}
                    disabled={isDeletingAccount}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleDeleteAccount}
                    disabled={isDeletingAccount}
                  >
                    {isDeletingAccount ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Deleting...
                      </>
                    ) : (
                      'Delete Account'
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
