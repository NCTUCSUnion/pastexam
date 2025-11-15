import { expect, type Locator, type Page } from '@playwright/test'

type ClickOptions = {
  timeout?: number
}

export const clickWhenVisible = async (locator: Locator, options?: ClickOptions) => {
  await expect(locator).toBeVisible({ timeout: options?.timeout })
  await locator.click()
}

export const acceptConfirmDialog = async (page: Page) => {
  const dialog = page.getByRole('alertdialog', { name: '刪除確認' })
  await expect(dialog).toBeVisible({ timeout: 5000 })

  const confirmButton = dialog.getByLabel('刪除')
  await clickWhenVisible(confirmButton, { timeout: 5000 })
  await expect(dialog).toBeHidden({ timeout: 5000 })
}
