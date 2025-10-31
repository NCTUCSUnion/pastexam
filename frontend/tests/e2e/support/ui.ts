import { expect, type Page } from '@playwright/test'

export const acceptConfirmDialog = async (
  page: Page,
) => {
  const dialog = page.getByRole('alertdialog', { name: '刪除確認' })
  await expect(dialog).toBeVisible({ timeout: 5000 })

  const confirmButton = dialog.getByLabel('刪除')
  await expect(confirmButton).toBeVisible({ timeout: 5000 })
  await confirmButton.click()
  await expect(dialog).toBeHidden({ timeout: 5000 })
}
