FasdUAS 1.101.10   ��   ��    k             l      ��  ��   

This script hook can be used for the "Save Document" hook.
It automatically saves the publications contained in a given static group to a given file whenever the document is saved.
You need to set the values for the GroupName and the OutputFilePath below manually.
     � 	 	 
 T h i s   s c r i p t   h o o k   c a n   b e   u s e d   f o r   t h e   " S a v e   D o c u m e n t "   h o o k . 
 I t   a u t o m a t i c a l l y   s a v e s   t h e   p u b l i c a t i o n s   c o n t a i n e d   i n   a   g i v e n   s t a t i c   g r o u p   t o   a   g i v e n   f i l e   w h e n e v e r   t h e   d o c u m e n t   i s   s a v e d . 
 Y o u   n e e d   t o   s e t   t h e   v a l u e s   f o r   t h e   G r o u p N a m e   a n d   t h e   O u t p u t F i l e P a t h   b e l o w   m a n u a l l y . 
   
  
 l     ��������  ��  ��        j     �� �� &0 thetemplatestring theTemplateString  m        �   d < $ p u b l i c a t i o n s > 
 < $ b i b T e X S t r i n g / > 
 < / $ p u b l i c a t i o n s > 
      w          i        I     ��  
�� .BDSKpActnull���     ****  o      ���� 0 thepubs thePubs  �� ��
�� 
fshk  o      ���� 0 thescripthook theScriptHook��    k     e       r         e        n        !   m    ��
�� 
docu ! o     ���� 0 thescripthook theScriptHook  o      ���� 0 thedoc theDoc   " # " l   ��������  ��  ��   #  $ % $ l   �� & '��   & 8 2 you may check the file name for the document here    ' � ( ( d   y o u   m a y   c h e c k   t h e   f i l e   n a m e   f o r   t h e   d o c u m e n t   h e r e %  ) * ) l   ��������  ��  ��   *  +�� + O    e , - , k    d . .  / 0 / l   ��������  ��  ��   0  1 2 1 l   �� 3 4��   3 U O you may also use another type of group, such as a field group or a smart group    4 � 5 5 �   y o u   m a y   a l s o   u s e   a n o t h e r   t y p e   o f   g r o u p ,   s u c h   a s   a   f i e l d   g r o u p   o r   a   s m a r t   g r o u p 2  6 7 6 l   ��������  ��  ��   7  8 9 8 r     : ; : e     < < 4    �� =
�� 
StGp = m     > > � ? ?  p r o j e c t 1 ; o      ���� 0 thegroup theGroup 9  @ A @ Z    6 B C���� B l    D���� D >    E F E o    ���� 0 thegroup theGroup F m    ��
�� 
msng��  ��   C k    2 G G  H I H r     J K J l    L���� L e     M M n     N O N 2   ��
�� 
bibi O o    ���� 0 thegroup theGroup��  ��   K o      ���� "0 thepublications thePublications I  P�� P I    2���� Q
�� .BDSKexptnull���     ****��   Q �� R S
�� 
usTx R o   " '���� &0 thetemplatestring theTemplateString S �� T U
�� 
to   T 4   ( ,�� V
�� 
psxf V m   * + W W � X X ^ / U s e r s / y o u r n a m e / W o r k s p a c e / p r o j e c t 1 / p r o j e c t 1 . b i b U �� Y��
�� 
for  Y o   - .���� "0 thepublications thePublications��  ��  ��  ��   A  Z [ Z l  7 7��������  ��  ��   [  \ ] \ r   7 > ^ _ ^ e   7 < ` ` 4   7 <�� a
�� 
StGp a m   9 : b b � c c  p r o j e c t 2 _ o      ���� 0 thegroup theGroup ]  d e d Z   ? b f g���� f l  ? B h���� h >  ? B i j i o   ? @���� 0 thegroup theGroup j m   @ A��
�� 
msng��  ��   g k   E ^ k k  l m l r   E K n o n l  E I p���� p e   E I q q n   E I r s r 2  F H��
�� 
bibi s o   E F���� 0 thegroup theGroup��  ��   o o      ���� "0 thepublications thePublications m  t�� t I  L ^���� u
�� .BDSKexptnull���     ****��   u �� v w
�� 
usTx v o   N S���� &0 thetemplatestring theTemplateString w �� x y
�� 
to   x 4   T X�� z
�� 
psxf z m   V W { { � | | ^ / U s e r s / y o u r n a m e / W o r k s p a c e / p r o j e c t 2 / p r o j e c t 2 . b i b y �� }��
�� 
for  } o   Y Z���� "0 thepublications thePublications��  ��  ��  ��   e  ~  ~ l  c c��������  ��  ��     ��� � l  c c��������  ��  ��  ��   - o    ���� 0 thedoc theDoc��   �                                                                                  BDSK  alis    &  Macintosh HD                   BD ����BibDesk.app                                                    ����            ����  
 cu             TeX   /:Applications:TeX:BibDesk.app/     B i b D e s k . a p p    M a c i n t o s h   H D  Applications/TeX/BibDesk.app  / ��     � � � l     ��������  ��  ��   �  � � � l     ��������  ��  ��   �  ��� � l     ��������  ��  ��  ��       �� �  ���   � ������ &0 thetemplatestring theTemplateString
�� .BDSKpActnull���     **** � �� ���� � ���
�� .BDSKpActnull���     ****�� 0 thepubs thePubs�� ������
�� 
fshk�� 0 thescripthook theScriptHook��   � ������������ 0 thepubs thePubs�� 0 thescripthook theScriptHook�� 0 thedoc theDoc�� 0 thegroup theGroup�� "0 thepublications thePublications � ���� >���������� W������ b {
�� 
docu
�� 
StGp
�� 
msng
�� 
bibi
�� 
usTx
�� 
to  
�� 
psxf
�� 
for �� 
�� .BDSKexptnull���     ****�� f��,EE�O� [*��/EE�O�� ��-EE�O*�b   �)��/�� Y hO*��/EE�O�� ��-EE�O*�b   �)��/�� Y hOPU ascr  ��ޭ