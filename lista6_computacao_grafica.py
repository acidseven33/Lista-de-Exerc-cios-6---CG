"""
Lista de Exercícios 6 – Computação Gráfica
Transformações de Modelagem, Visualização e Projeção

Dependências:
    pip install PyOpenGL PyOpenGL_accelerate

Execução:
    python lista6.py

Controles:
    G       mostrar/ocultar a grade
    X / Z   rotacionar a grade em torno do eixo X (+/-)
    O       projeção ortogonal
    P       projeção perspectiva
    R       restaurar a grade
    A / D   girar o primeiro elo do robô
    W / S   girar o segundo elo do robô
    Q / E   girar o terceiro elo do robô
    B       abrir/fechar a garra
    setas   azimute e incidência da câmera
    PageUp/PageDown   aproximar/afastar a câmera
    Ctrl + setas      movimentação mais rápida da câmera
    Alt + setas       ajuste fino da câmera
    Shift + setas     alterar o twist (rolagem) da câmera
    ESC     sair

Observação:
    A grade está no plano XY (z=0). A rotação em torno de X inclina
    esse plano em relação à câmera, permitindo observar a diferença
    entre as projeções ortogonal e perspectiva.
"""

import math
import sys

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


# --------------------------- Estado da aplicação ---------------------------

largura, altura = 1000, 700

angulo_grade_x = 0.0
mostrar_grade = True
projecao_perspectiva = True

# Ângulos dos três elos do braço robótico
angulo_braco_1 = 25.0
angulo_braco_2 = -35.0
angulo_braco_3 = 20.0
garra_aberta = True

# Câmera em coordenadas polares/esféricas
camera_azimute = 45.0       # rotação ao redor do eixo vertical Y
camera_incidencia = 32.0    # ângulo em relação ao plano horizontal
camera_twist = 0.0          # rolagem ao redor do eixo de visão
camera_distancia = 13.0

angulo_garra = 25.0


# ------------------------------- Utilidades --------------------------------

def limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def desenhar_texto(x, y, texto):
    """Desenha texto 2D na janela."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, largura, 0, altura)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(0.95, 0.95, 0.95)
    glRasterPos2f(x, y)
    for caractere in texto:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(caractere))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def vetor_normalizado(v):
    norma = math.sqrt(sum(c * c for c in v))
    if norma == 0:
        return v
    return tuple(c / norma for c in v)


def rotacionar_vetor_eixo(v, eixo, angulo_graus):
    """Rotação de Rodrigues: gira v ao redor de eixo."""
    a = math.radians(angulo_graus)
    eixo = vetor_normalizado(eixo)
    cos_a, sin_a = math.cos(a), math.sin(a)
    produto_escalar = sum(v[i] * eixo[i] for i in range(3))
    cruzado = (
        eixo[1] * v[2] - eixo[2] * v[1],
        eixo[2] * v[0] - eixo[0] * v[2],
        eixo[0] * v[1] - eixo[1] * v[0],
    )
    return tuple(
        v[i] * cos_a + cruzado[i] * sin_a
        + eixo[i] * produto_escalar * (1 - cos_a)
        for i in range(3)
    )


# ------------------------------ Câmera polar -------------------------------

def configurar_camera():
    az = math.radians(camera_azimute)
    inc = math.radians(camera_incidencia)

    # Posição calculada a partir de distância, azimute e incidência.
    x = camera_distancia * math.cos(inc) * math.sin(az)
    y = camera_distancia * math.sin(inc)
    z = camera_distancia * math.cos(inc) * math.cos(az)

    posicao = (x, y, z)
    direcao = vetor_normalizado((-x, -y, -z))

    # Vetor para cima inicial, corrigido para não ficar paralelo à visão.
    referencia_up = (0.0, 1.0, 0.0)
    direita = (
        direcao[1] * referencia_up[2] - direcao[2] * referencia_up[1],
        direcao[2] * referencia_up[0] - direcao[0] * referencia_up[2],
        direcao[0] * referencia_up[1] - direcao[1] * referencia_up[0],
    )
    direita = vetor_normalizado(direita)
    cima = (
        direita[1] * direcao[2] - direita[2] * direcao[1],
        direita[2] * direcao[0] - direita[0] * direcao[2],
        direita[0] * direcao[1] - direita[1] * direcao[0],
    )
    cima = vetor_normalizado(cima)

    # Twist: gira o vetor "up" ao redor da direção de visão.
    cima = rotacionar_vetor_eixo(cima, direcao, camera_twist)

    gluLookAt(
        posicao[0], posicao[1], posicao[2],
        0.0, 0.0, 0.0,
        cima[0], cima[1], cima[2]
    )


def configurar_projecao():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    proporcao = largura / float(max(altura, 1))
    if projecao_perspectiva:
        gluPerspective(55.0, proporcao, 0.1, 100.0)
    else:
        tamanho = camera_distancia * 0.72
        glOrtho(
            -tamanho * proporcao, tamanho * proporcao,
            -tamanho, tamanho,
            -100.0, 100.0
        )

    glMatrixMode(GL_MODELVIEW)


# --------------------------------- Grade ------------------------------------

def desenhar_grade():
    """Desenha uma grade 10 x 6 no plano XY."""
    glPushMatrix()
    glRotatef(angulo_grade_x, 1.0, 0.0, 0.0)

    glLineWidth(1.5)
    glColor3f(0.72, 0.78, 0.82)
    glBegin(GL_LINES)

    # Linhas paralelas ao eixo Y
    for x in range(-5, 6):
        glVertex3f(x, -3, 0)
        glVertex3f(x, 3, 0)

    # Linhas paralelas ao eixo X
    for y in range(-3, 4):
        glVertex3f(-5, y, 0)
        glVertex3f(5, y, 0)

    glEnd()

    # Eixos coordenados
    glLineWidth(2.5)
    glBegin(GL_LINES)
    glColor3f(1.0, 0.15, 0.15)  # X vermelho
    glVertex3f(0, 0, 0.02)
    glVertex3f(6, 0, 0.02)
    glColor3f(0.2, 1.0, 0.25)   # Y verde
    glVertex3f(0, 0, 0.02)
    glVertex3f(0, 4, 0.02)
    glColor3f(0.2, 0.45, 1.0)   # Z azul
    glVertex3f(0, 0, 0.02)
    glVertex3f(0, 0, 3)
    glEnd()

    glPopMatrix()


# ------------------------------ Braço robô ---------------------------------

def desenhar_cubo_elo(comprimento, largura_elo, altura_elo):
    """Desenha um elo cujo início está na origem e cujo comprimento segue +X."""
    glPushMatrix()
    glTranslatef(comprimento / 2.0, 0, 0)
    glScalef(comprimento, largura_elo, altura_elo)
    glutSolidCube(1.0)
    glPopMatrix()


def desenhar_articulacao(raio=0.22):
    glutSolidSphere(raio, 18, 14)


def desenhar_braco():
    global angulo_garra

    glPushMatrix()
    # Base fixa do robô
    glTranslatef(-3.2, -2.0, 0.35)

    glColor3f(0.25, 0.48, 0.78)
    glPushMatrix()
    glScalef(0.9, 0.9, 0.55)
    glutSolidCube(1.0)
    glPopMatrix()

    # Primeiro elo
    glTranslatef(0, 0, 0.35)
    glRotatef(angulo_braco_1, 0, 0, 1)
    glColor3f(0.95, 0.62, 0.18)
    desenhar_articulacao()
    desenhar_cubo_elo(2.0, 0.38, 0.38)

    glTranslatef(2.0, 0, 0)
    glRotatef(angulo_braco_2, 0, 0, 1)
    glColor3f(0.90, 0.78, 0.28)
    desenhar_articulacao()
    desenhar_cubo_elo(1.7, 0.32, 0.32)

    glTranslatef(1.7, 0, 0)
    glRotatef(angulo_braco_3, 0, 0, 1)
    glColor3f(0.25, 0.72, 0.55)
    desenhar_articulacao()
    desenhar_cubo_elo(0.65, 0.25, 0.25)

    # Garra: duas hastes independentes, transformadas a partir da ponta.
    glTranslatef(0.65, 0, 0)
    abertura = angulo_garra if garra_aberta else 2.0

    glColor3f(0.88, 0.9, 0.94)
    for lado in (-1, 1):
        glPushMatrix()
        glRotatef(lado * abertura, 0, 0, 1)
        glTranslatef(0.42, 0, 0)
        glScalef(0.85, 0.12, 0.16)
        glutSolidCube(1.0)
        glPopMatrix()

    glPopMatrix()


# -------------------------------- Render ------------------------------------

def desenhar_cena():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    configurar_projecao()

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    configurar_camera()

    # Plano de referência discreto
    glDisable(GL_LIGHTING)
    if mostrar_grade:
        desenhar_grade()

    desenhar_braco()

    modo = "Perspectiva" if projecao_perspectiva else "Ortogonal"
    desenhar_texto(12, altura - 22, f"Projecao: {modo} | Grade X: {angulo_grade_x:.0f} graus")
    desenhar_texto(12, altura - 42, "O/P: projecao | X/Z: girar grade | A/D, W/S, Q/E: braco | B: garra")
    desenhar_texto(12, altura - 62, "Setas: camera | Ctrl: rapido | Alt: fino | Shift: twist | PgUp/PgDn: distancia")

    glutSwapBuffers()


# ------------------------------ Interação ----------------------------------

def teclado(tecla, x, y):
    global mostrar_grade, projecao_perspectiva, angulo_grade_x
    global angulo_braco_1, angulo_braco_2, angulo_braco_3, garra_aberta

    tecla = tecla.decode("utf-8", errors="ignore").lower()

    if tecla == '\x1b':
        sys.exit(0)
    elif tecla == 'g':
        mostrar_grade = not mostrar_grade
    elif tecla == 'x':
        angulo_grade_x = (angulo_grade_x + 5.0) % 360
    elif tecla == 'z':
        angulo_grade_x = (angulo_grade_x - 5.0) % 360
    elif tecla == 'o':
        projecao_perspectiva = False
    elif tecla == 'p':
        projecao_perspectiva = True
    elif tecla == 'r':
        angulo_grade_x = 0.0
    elif tecla == 'a':
        angulo_braco_1 += 5
    elif tecla == 'd':
        angulo_braco_1 -= 5
    elif tecla == 'w':
        angulo_braco_2 += 5
    elif tecla == 's':
        angulo_braco_2 -= 5
    elif tecla == 'q':
        angulo_braco_3 += 5
    elif tecla == 'e':
        angulo_braco_3 -= 5
    elif tecla == 'b':
        garra_aberta = not garra_aberta

    glutPostRedisplay()


def teclado_especial(tecla, x, y):
    global camera_azimute, camera_incidencia, camera_distancia, camera_twist

    modificadores = glutGetModifiers()
    passo = 8.0
    if modificadores & GLUT_ACTIVE_CTRL:
        passo = 18.0
    elif modificadores & GLUT_ACTIVE_ALT:
        passo = 2.0

    if tecla == GLUT_KEY_LEFT:
        if modificadores & GLUT_ACTIVE_SHIFT:
            camera_twist -= passo
        else:
            camera_azimute -= passo
    elif tecla == GLUT_KEY_RIGHT:
        if modificadores & GLUT_ACTIVE_SHIFT:
            camera_twist += passo
        else:
            camera_azimute += passo
    elif tecla == GLUT_KEY_UP:
        if modificadores & GLUT_ACTIVE_SHIFT:
            camera_twist += passo
        else:
            camera_incidencia = limitar(camera_incidencia + passo, -85, 85)
    elif tecla == GLUT_KEY_DOWN:
        if modificadores & GLUT_ACTIVE_SHIFT:
            camera_twist -= passo
        else:
            camera_incidencia = limitar(camera_incidencia - passo, -85, 85)
    elif tecla == GLUT_KEY_PAGE_UP:
        camera_distancia = max(3.0, camera_distancia - 0.7)
    elif tecla == GLUT_KEY_PAGE_DOWN:
        camera_distancia = min(35.0, camera_distancia + 0.7)

    glutPostRedisplay()


def redimensionar(nova_largura, nova_altura):
    global largura, altura
    largura = max(1, nova_largura)
    altura = max(1, nova_altura)
    glViewport(0, 0, largura, altura)
    glutPostRedisplay()


# --------------------------------- Main -------------------------------------

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(largura, altura)
    glutInitWindowPosition(80, 50)
    glutCreateWindow(b"Computacao Grafica - Lista 6")

    glClearColor(0.08, 0.09, 0.12, 1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)

    glutDisplayFunc(desenhar_cena)
    glutReshapeFunc(redimensionar)
    glutKeyboardFunc(teclado)
    glutSpecialFunc(teclado_especial)

    glutMainLoop()


if __name__ == "__main__":
    main()
