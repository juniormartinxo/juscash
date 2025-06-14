import { Request, Response } from 'express'
import { LoginUserUseCase } from '../../../application/usecases/auth/login-user.usecase'
import { LogoutUseCase } from '../../../application/usecases/auth/logout.usecase'
import { RefreshTokenUseCase } from '../../../application/usecases/auth/refresh-token.usecase'
import { RegisterUserUseCase } from '../../../application/usecases/auth/register-user.usecase'
import { ApiResponseBuilder } from '../../../shared/utils/api-response'
import { asyncHandler } from '../../../shared/utils/async-handler'

export class AuthController {
  constructor(
    private registerUserUseCase: RegisterUserUseCase,
    private loginUserUseCase: LoginUserUseCase,
    private refreshTokenUseCase: RefreshTokenUseCase,
    private logoutUseCase: LogoutUseCase
  ) { }

  register = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { name, email, password } = req.body

    const result = await this.registerUserUseCase.execute({
      name,
      email,
      password,
    })

    res.status(201).json(ApiResponseBuilder.success(result))
  });

  login = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { email, password } = req.body

    const result = await this.loginUserUseCase.execute({
      email,
      password,
    })

    res.json(ApiResponseBuilder.success(result))
  });

  refresh = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { refreshToken } = req.body

    if (!refreshToken) {
      res.status(400).json(ApiResponseBuilder.error('Refresh token is required'))
      return
    }

    const result = await this.refreshTokenUseCase.execute({ refreshToken })

    res.json(ApiResponseBuilder.success(result))
  });

  logout = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const authHeader = req.headers.authorization
    const accessToken = authHeader?.substring(7) // Remove 'Bearer '

    if (!accessToken) {
      res.status(400).json(ApiResponseBuilder.error('Access token is required'))
      return
    }

    const result = await this.logoutUseCase.execute({ accessToken })

    res.json(ApiResponseBuilder.success(result))
  });
}
