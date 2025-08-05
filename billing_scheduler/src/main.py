import asyncio
import logging
from check_transactions import check_transactions
from check_subscription_expiration import check_subscription_expiration
from delete_expired_subscription import delete_expired_subscription
from check_role_existence import check_role_existence


async def safe_execute(func, func_name: str):
    """Безопасное выполнение функции с обработкой ошибок"""
    try:
        await func()
    except Exception as e:
        logging.error("Ошибка при выполнении %s: %s", func_name, e)


async def main():
    logging.info("Запуск billing-scheduler")

    while True:
        try:
            await safe_execute(check_transactions, "check_transactions")
            await safe_execute(check_subscription_expiration, "check_subscription_expiration")
            await safe_execute(delete_expired_subscription, "delete_expired_subscription")
            await safe_execute(check_role_existence, "check_role_existence")

        except Exception as e:
            logging.error("Критическая ошибка в main loop: %s", e)

        # Ждем перед следующей итерацией
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
